"""Small deterministic in-memory dataset for the first milestone."""

PRODUCTS = [
    {
        "product_id": "P-100",
        "name": "Wireless Mouse",
        "category": "Computer Accessories",
        "unit_price": 249.99,
        "sku": "MOU-WL-100",
    },
    {
        "product_id": "P-200",
        "name": "USB-C Hub",
        "category": "Computer Accessories",
        "unit_price": 499.00,
        "sku": "HUB-USBC-200",
    },
    {
        "product_id": "P-300",
        "name": "Laptop Stand",
        "category": "Office Accessories",
        "unit_price": 329.50,
        "sku": "STD-LAP-300",
    },
]

INVENTORY = [
    {"product_id": "P-100", "store_id": "STORE-01", "available_quantity": 18, "reserved_quantity": 2},
    {"product_id": "P-200", "store_id": "STORE-01", "available_quantity": 4, "reserved_quantity": 1},
    {"product_id": "P-300", "store_id": "STORE-01", "available_quantity": 0, "reserved_quantity": 0},
]

ORDERS = [
    {
        "order_id": "ORD-1001",
        "customer_id": "C-001",
        "status": "shipped",
        "items": [{"product_id": "P-100", "quantity": 2}],
    },
    {
        "order_id": "ORD-1002",
        "customer_id": "C-002",
        "status": "processing",
        "items": [
            {"product_id": "P-100", "quantity": 3},
            {"product_id": "P-200", "quantity": 1},
        ],
    },
    {
        "order_id": "ORD-1003",
        "customer_id": "C-003",
        "status": "delivered",
        "items": [{"product_id": "P-300", "quantity": 1}],
    },
]

REFUND_POLICY = {
    "return_window_days": 30,
    "requires_approval": True,
    "notes": "Refund eligibility must be checked against order status and return-window evidence.",
}
