
"""Read-only retail tools backed by PostgreSQL."""

import json
from typing import Any

import psycopg
from langchain.tools import tool

from app.db import get_db_connection


def _json(data: Any) -> str:
    """Serialize query results, including database dates and decimals."""
    return json.dumps(data, ensure_ascii=False, default=str)


def _normalise_id(value: str) -> str:
    """Normalise Olist UUIDs without changing their case-sensitive contents."""
    return value.strip().lower()


def lookup_products(query: str = "", limit: int = 10) -> str:
    """Search Olist products by product ID or translated category."""
    q = query.strip()
    pattern = f"%{q}%"


    sql = """
        SELECT
            p.product_id,
            p.product_category_name,
            t.product_category_name_english AS category_english,
            COALESCE(
                t.product_category_name_english,
                p.product_category_name
            ) AS category
        FROM products AS p
        LEFT JOIN product_category_name_translation AS t
            ON p.product_category_name = t.product_category_name
        WHERE %s = ''
        OR p.product_id ILIKE %s
        OR p.product_category_name ILIKE %s
        OR t.product_category_name_english ILIKE %s
        ORDER BY p.product_id
        LIMIT %s;
    """


    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (q, pattern, pattern, pattern, limit),
                )
                rows = cursor.fetchall()

        return _json({"count": len(rows), "products": rows})
    except psycopg.Error:
        return _json({
            "error": "database_error",
            "message": "Product search could not be completed.",
        })


def get_inventory(
    product_id: str,
    store_id: str = "STORE-01",
) -> str:
    """Get available and reserved stock for a product at a store."""
    pid = _normalise_id(product_id)
    sid = store_id.strip().upper()

    product_sql = """
        SELECT
            p.product_id,
            COALESCE(
                t.product_category_name_english,
                p.product_category_name
            ) AS category
        FROM products AS p
        LEFT JOIN product_category_name_translation AS t
            ON p.product_category_name = t.product_category_name
        WHERE p.product_id = %s;
    """

    inventory_sql = """
        SELECT product_id, store_id, available_quantity,
               reserved_quantity, updated_at
        FROM inventory
        WHERE product_id = %s AND store_id = %s;
    """

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(product_sql, (pid,))
                product = cursor.fetchone()

                if product is None:
                    return _json({
                        "error": "unknown_product",
                        "product_id": pid,
                    })

                cursor.execute(inventory_sql, (pid, sid))
                stock = cursor.fetchone()

        if stock is None:
            return _json({
                "error": "inventory_not_found",
                "product_id": pid,
                "store_id": sid,
            })

        return _json({"product": product, **stock})

    except psycopg.Error as exc:
        print(f"Inventory lookup database error: {exc!r}")
        return _json({
            "error": "database_error",
            "message": "Inventory lookup could not be completed.",
        })
    # except psycopg.Error as exc:
    #     print(f"Inventory lookup database error: {exc!r}")
    #     return _json({
    #         "error": "database_error",
    #         "message": str(exc),
    #     })


def get_order(order_id: str) -> str:
    """Retrieve an Olist order and its associated order-item rows."""
    oid = _normalise_id(order_id)

    order_sql = """
        SELECT order_id, customer_id, order_status,
               order_purchase_timestamp, order_approved_at,
               order_delivered_carrier_date,
               order_delivered_customer_date,
               order_estimated_delivery_date
        FROM orders
        WHERE order_id = %s;
    """

    items_sql = """
        SELECT order_item_id, product_id, seller_id,
               shipping_limit_date, price, freight_value
        FROM order_items
        WHERE order_id = %s
        ORDER BY order_item_id;
    """

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(order_sql, (oid,))
                order = cursor.fetchone()

                if order is None:
                    return _json({
                        "error": "order_not_found",
                        "order_id": oid,
                    })

                cursor.execute(items_sql, (oid,))
                items = cursor.fetchall()

        return _json({**order, "items": items})

    except psycopg.Error:
        return _json({
            "error": "database_error",
            "message": "Order lookup could not be completed.",
        })


def check_fulfilment(
    order_id: str,
    store_id: str = "STORE-01",
) -> str:
    """Check if available stock covers every item in an Olist order."""
    oid = _normalise_id(order_id)
    sid = store_id.strip().upper()

    order_sql = """
        SELECT order_id
        FROM orders
        WHERE order_id = %s;
    """

    # In Olist, each row in order_items represents one ordered item.
    # Count rows per product to calculate the quantity required.
    fulfilment_sql = """
    SELECT
        oi.product_id,
        COUNT(*)::INTEGER AS quantity_required,
        i.available_quantity AS quantity_available,
        (i.product_id IS NOT NULL) AS inventory_record_found
    FROM order_items AS oi
    LEFT JOIN inventory AS i
        ON i.product_id = oi.product_id
       AND i.store_id = %s
    WHERE oi.order_id = %s
    GROUP BY
        oi.product_id,
        i.product_id,
        i.available_quantity
    ORDER BY oi.product_id;
"""

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(order_sql, (oid,))
                order = cursor.fetchone()

                if order is None:
                    return _json({
                        "error": "order_not_found",
                        "order_id": oid,
                    })

                cursor.execute(fulfilment_sql, (sid, oid))
                rows = cursor.fetchall()

        lines = []


        for row in rows:
            inventory_found = row["inventory_record_found"]
            available = row["quantity_available"]

            enough = (
                inventory_found
                and available is not None
                and available >= row["quantity_required"]
            )

            lines.append({
                "product_id": row["product_id"],
                "quantity_required": row["quantity_required"],
                "quantity_available": available,
                "inventory_record_found": inventory_found,
                "sufficient": enough,
            })

        return _json({
            "order_id": oid,
            "store_id": sid,
            "can_fulfil": bool(lines) and all(
                line["sufficient"] for line in lines
            ),
            "lines": lines,
        })

    except psycopg.Error:
        return _json({
            "error": "database_error",
            "message": "Fulfilment check could not be completed.",
        })


@tool
def product_search(query: str = "") -> str:
    """Search products by product ID or product category."""
    return lookup_products(query)


@tool
def inventory_lookup(
    product_id: str,
    store_id: str = "STORE-01",
) -> str:
    """Look up stock by product ID and store; defaults to STORE-01."""
    return get_inventory(product_id, store_id)


@tool
def order_lookup(order_id: str) -> str:
    """Retrieve an order and its items using its order ID."""
    return get_order(order_id)


@tool
def fulfilment_check(
    order_id: str,
    store_id: str = "STORE-01",
) -> str:
    """Check whether available store stock covers every order item."""
    return check_fulfilment(order_id, store_id)


AGENT_TOOLS = [
    product_search,
    inventory_lookup,
    order_lookup,
    fulfilment_check,
]
