"""Mock data for FastMCP order and inventory servers."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Order data (mirrors init_db.sql seed rows with extra shipping metadata)
# ---------------------------------------------------------------------------
ORDERS: dict[str, dict] = {
    "ORD-001": {
        "order_id": "ORD-001",
        "customer_name": "Priya Sharma",
        "status": "shipped",
        "product_id": "PRD-101",
        "product_name": "Wireless Headphones",
        "quantity": 1,
        "shipping_carrier": "BlueDart",
        "tracking_number": "BD1234567890",
        "estimated_delivery": "2026-06-20",
        "created_at": "2026-06-10",
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "customer_name": "Rahul Menon",
        "status": "delivered",
        "product_id": "PRD-102",
        "product_name": "Mechanical Keyboard",
        "quantity": 2,
        "shipping_carrier": "DTDC",
        "tracking_number": "DT9876543210",
        "delivered_at": "2026-06-15",
        "created_at": "2026-06-08",
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "customer_name": "Anika Bose",
        "status": "cancelled",
        "product_id": "PRD-103",
        "product_name": "USB-C Hub",
        "quantity": 1,
        "cancellation_reason": "Customer requested",
        "created_at": "2026-06-12",
    },
    "ORD-004": {
        "order_id": "ORD-004",
        "customer_name": "Dev Nair",
        "status": "processing",
        "product_id": "PRD-101",
        "product_name": "Wireless Headphones",
        "quantity": 3,
        "estimated_ship_date": "2026-06-18",
        "created_at": "2026-06-16",
    },
    "ORD-005": {
        "order_id": "ORD-005",
        "customer_name": "Sara Pillai",
        "status": "shipped",
        "product_id": "PRD-102",
        "product_name": "Mechanical Keyboard",
        "quantity": 1,
        "shipping_carrier": "Delhivery",
        "tracking_number": "DL5678901234",
        "estimated_delivery": "2026-06-19",
        "created_at": "2026-06-11",
    },
}

# ---------------------------------------------------------------------------
# Inventory data with variant-level stock breakdown
# ---------------------------------------------------------------------------
INVENTORY: dict[str, dict] = {
    "PRD-101": {
        "product_id": "PRD-101",
        "name": "Wireless Headphones",
        "total_stock": 50,
        "available": 47,
        "reserved": 3,
        "variants": [
            {"color": "Black", "stock": 20},
            {"color": "White", "stock": 15},
            {"color": "Navy Blue", "stock": 12},
        ],
    },
    "PRD-102": {
        "product_id": "PRD-102",
        "name": "Mechanical Keyboard",
        "total_stock": 0,
        "available": 0,
        "reserved": 0,
        "restock_date": "2026-06-25",
        "variants": [
            {"switch": "Red", "stock": 0},
            {"switch": "Blue", "stock": 0},
            {"switch": "Brown", "stock": 0},
        ],
    },
    "PRD-103": {
        "product_id": "PRD-103",
        "name": "USB-C Hub",
        "total_stock": 20,
        "available": 20,
        "reserved": 0,
        "variants": [
            {"ports": "7-in-1", "stock": 12},
            {"ports": "10-in-1", "stock": 8},
        ],
    },
    "PRD-104": {
        "product_id": "PRD-104",
        "name": "Webcam 4K",
        "total_stock": 15,
        "available": 15,
        "reserved": 0,
        "variants": [
            {"mount": "Clip", "stock": 10},
            {"mount": "Tripod", "stock": 5},
        ],
    },
    "PRD-105": {
        "product_id": "PRD-105",
        "name": "Old Mouse",
        "total_stock": 0,
        "available": 0,
        "reserved": 0,
        "discontinued": True,
    },
}

# ---------------------------------------------------------------------------
# Special IDs for error simulation
# ---------------------------------------------------------------------------
SIMULATE_TIMEOUT_ORDER_ID = "ORD-999"   # triggers timeout
SIMULATE_ERROR_ORDER_ID = "ORD-888"     # triggers internal error
