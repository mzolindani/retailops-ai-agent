"""Read-only retail tools exposed to the agent."""

import json
from typing import Any

from langchain.tools import tool

from app.data.retail_data import INVENTORY, ORDERS, PRODUCTS


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def lookup_products(query: str = "") -> str:
    """Search the product catalogue by product name, category, SKU, or product ID."""
    q = query.strip().lower()
    matches = [
        p for p in PRODUCTS
        if not q or q in p["name"].lower()
        or q in p["category"].lower()
        or q in p["sku"].lower()
        or q in p["product_id"].lower()
    ]
    return _json({"count": len(matches), "products": matches})


def get_inventory(product_id: str, store_id: str = "STORE-01") -> str:
    """Get current inventory for a product at a store using its product ID."""
    pid = product_id.strip().upper()
    sid = store_id.strip().upper()
    product = next((p for p in PRODUCTS if p["product_id"] == pid), None)
    if product is None:
        return _json({"error": "unknown_product", "product_id": pid})
    row = next(
        (r for r in INVENTORY if r["product_id"] == pid and r["store_id"] == sid),
        None,
    )
    if row is None:
        return _json({"error": "inventory_not_found", "product_id": pid, "store_id": sid})
    return _json({"product": product["name"], **row})


def get_order(order_id: str) -> str:
    """Retrieve an order by its order ID, including status and product quantities."""
    oid = order_id.strip().upper()
    order = next((o for o in ORDERS if o["order_id"] == oid), None)
    if order is None:
        return _json({"error": "order_not_found", "order_id": oid})
    return _json(order)


def check_fulfilment(order_id: str, store_id: str = "STORE-01") -> str:
    """Check whether current available stock can fulfil every line in an order."""
    oid = order_id.strip().upper()
    order = next((o for o in ORDERS if o["order_id"] == oid), None)
    if order is None:
        return _json({"error": "order_not_found", "order_id": oid})

    lines = []
    all_available = True
    for item in order["items"]:
        product = next((p for p in PRODUCTS if p["product_id"] == item["product_id"]), None)
        stock = next(
            (r for r in INVENTORY
             if r["product_id"] == item["product_id"] and r["store_id"] == store_id.upper()),
            None,
        )
        available = stock["available_quantity"] if stock else 0
        needed = item["quantity"]
        enough = available >= needed
        all_available = all_available and enough
        lines.append({
            "product_id": item["product_id"],
            "product_name": product["name"] if product else "Unknown product",
            "quantity_required": needed,
            "quantity_available": available,
            "sufficient": enough,
        })
    return _json({
        "order_id": oid,
        "store_id": store_id.upper(),
        "can_fulfil": all_available,
        "lines": lines,
    })


@tool
def product_search(query: str = "") -> str:
    """Search products by name, category, SKU, or product ID."""
    return lookup_products(query)


@tool
def inventory_lookup(product_id: str, store_id: str = "STORE-01") -> str:
    """Look up inventory using a product ID. Defaults to store STORE-01."""
    return get_inventory(product_id, store_id)


@tool
def order_lookup(order_id: str) -> str:
    """Look up an order by its ID, such as ORD-1002."""
    return get_order(order_id)


@tool
def fulfilment_check(order_id: str, store_id: str = "STORE-01") -> str:
    """Check whether the store has enough stock for every item in an order."""
    return check_fulfilment(order_id, store_id)


AGENT_TOOLS = [product_search, inventory_lookup, order_lookup, fulfilment_check]
