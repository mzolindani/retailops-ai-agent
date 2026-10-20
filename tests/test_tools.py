import json
from unittest.mock import MagicMock, patch

from app.tools import (
    check_fulfilment,
    get_inventory,
    get_order,
    lookup_products,
)


def mock_database():
    """Create a mocked PostgreSQL connection and cursor."""
    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


def test_product_search_returns_category_matches():
    connection, cursor = mock_database()

    cursor.fetchall.return_value = [
        {
            "product_id": "product-123",
            "product_category_name": "utilidades_domesticas",
            "category_english": "housewares",
            "category": "housewares",
        }
    ]

    with patch("app.tools.get_db_connection", return_value=connection):
        result = json.loads(lookup_products("housewares", 5))

    assert result["count"] == 1
    assert result["products"][0]["category"] == "housewares"
    assert result["products"][0]["product_id"] == "product-123"


def test_inventory_lookup_returns_known_quantity():
    connection, cursor = mock_database()

    cursor.fetchone.side_effect = [
        {
            "product_id": "product-123",
            "category": "housewares",
        },
        {
            "product_id": "product-123",
            "store_id": "STORE-01",
            "available_quantity": 18,
            "reserved_quantity": 2,
            "updated_at": None,
        },
    ]

    with patch("app.tools.get_db_connection", return_value=connection):
        result = json.loads(
            get_inventory("product-123", "STORE-01")
        )

    assert result["available_quantity"] == 18
    assert result["reserved_quantity"] == 2
    assert result["store_id"] == "STORE-01"


def test_unknown_order_returns_structured_error():
    connection, cursor = mock_database()
    cursor.fetchone.return_value = None

    with patch("app.tools.get_db_connection", return_value=connection):
        result = json.loads(get_order("unknown-order-id"))

    assert result["error"] == "order_not_found"


def test_order_can_be_fulfilled_when_stock_is_sufficient():
    connection, cursor = mock_database()

    cursor.fetchone.return_value = {"order_id": "order-123"}
    cursor.fetchall.return_value = [
        {
            "product_id": "product-123",
            "quantity_required": 2,
            "quantity_available": 5,
        },
        {
            "product_id": "product-456",
            "quantity_required": 3,
            "quantity_available": 3,
        },
    ]

    with patch("app.tools.get_db_connection", return_value=connection):
        result = json.loads(
            check_fulfilment("order-123", "STORE-01")
        )

    assert result["can_fulfil"] is True
    assert all(line["sufficient"] for line in result["lines"])


def test_order_cannot_be_fulfilled_when_stock_is_insufficient():
    connection, cursor = mock_database()

    cursor.fetchone.return_value = {"order_id": "order-456"}
    cursor.fetchall.return_value = [
        {
            "product_id": "product-789",
            "quantity_required": 3,
            "quantity_available": 0,
        }
    ]

    with patch("app.tools.get_db_connection", return_value=connection):
        result = json.loads(
            check_fulfilment("order-456", "STORE-01")
        )

    assert result["can_fulfil"] is False
    assert result["lines"][0]["quantity_available"] == 0
    assert result["lines"][0]["sufficient"] is False