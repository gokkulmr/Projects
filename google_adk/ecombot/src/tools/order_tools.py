import re
from google.adk.tools import ToolContext

MOCK_ORDERS = {
    "ORD-001": {
        "order_id": "ORD-001",
        "status": "Shipped",
        "eta": "5 Jun 2026",
        "carrier": "BlueDart",
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "status": "Processing",
        "eta": "7 Jun 2026",
        "carrier": "DTDC",
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "status": "Delivered",
        "eta": "Already delivered",
        "carrier": "FedEx",
    },
}


def get_order_status(order_id: str, tool_context: ToolContext) -> dict:

    # validate format
    if not re.fullmatch(r"ORD-\d{3}", order_id):
        return {"error": "Invalid order ID format."}

    order = MOCK_ORDERS.get(order_id)

    if not order:
        return {"error": f"Order {order_id} not found."}

    # STORE IN SESSION STATE (IMPORTANT)
    tool_context.state["last_order_id"] = order_id

    return order