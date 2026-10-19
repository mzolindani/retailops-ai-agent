import json

from app.tools import check_fulfilment, get_inventory, get_order, lookup_products


def test_product_search_finds_wireless_mouse():
    result = json.loads(lookup_products("wireless mouse"))
    assert result["count"] == 1
    assert result["products"][0]["product_id"] == "P-100"


def test_inventory_lookup_returns_known_quantity():
    result = json.loads(get_inventory("P-100"))
    assert result["available_quantity"] == 18


def test_unknown_order_returns_structured_error():
    result = json.loads(get_order("ORD-9999"))
    assert result["error"] == "order_not_found"


def test_order_1002_can_be_fulfilled():
    result = json.loads(check_fulfilment("ORD-1002"))
    assert result["can_fulfil"] is True
    assert all(line["sufficient"] for line in result["lines"])


def test_order_1003_cannot_be_fulfilled():
    result = json.loads(check_fulfilment("ORD-1003"))
    assert result["can_fulfil"] is False
    assert result["lines"][0]["quantity_available"] == 0
