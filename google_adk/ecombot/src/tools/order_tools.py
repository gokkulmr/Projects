"""Order lookup and modification tools backed by PostgreSQL."""

from __future__ import annotations

import re
from typing import Any

from services.db import fetch_one, execute, DatabaseServiceError

try:
    from google.adk.tools import ToolContext  # type: ignore
    from google.adk.tools import tool  # type: ignore
except Exception:
    def tool(func):  # type: ignore
        return func

    class ToolContext:  # type: ignore
        state: dict[str, Any]


@tool
def get_order_status(order_id: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Retrieve the status and details of an order."""
    if not re.fullmatch(r"ORD-\d{3}", order_id):
        return {"ok": False, "error": "Invalid order ID format. Expected format: ORD-XXX"}

    try:
        query = "SELECT order_id, customer_name, status, product_id, quantity, created_at FROM orders WHERE order_id = %s"
        row = fetch_one(query, (order_id,))
    except DatabaseServiceError:
        return {"ok": False, "error": "Order service is temporarily unavailable."}

    if not row:
        return {"ok": False, "error": f"Order {order_id} not found."}

    # Serialize datetime / Decimal objects for JSON-safe tool output
    safe_row = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            safe_row[k] = v.isoformat()
        elif hasattr(v, "as_integer_ratio"):  # Decimal
            safe_row[k] = float(v)
        else:
            safe_row[k] = v

    if tool_context is not None:
        tool_context.state["last_order_id"] = order_id
        tool_context.state["last_intent"] = "order_lookup"

    return {
        "ok": True,
        "results": safe_row,
    }


@tool
def cancel_order(order_id: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Cancel an existing order if it has not shipped yet."""
    if not re.fullmatch(r"ORD-\d{3}", order_id):
        return {"ok": False, "error": "Invalid order ID format. Expected format: ORD-XXX"}

    try:
        # First check if the order exists and its current status
        check_query = "SELECT status FROM orders WHERE order_id = %s"
        row = fetch_one(check_query, (order_id,))
        
        if not row:
            return {"ok": False, "error": f"Order {order_id} not found."}
            
        current_status = row.get("status", "").lower()
        if current_status in ["shipped", "delivered"]:
             return {"ok": False, "error": f"Cannot cancel order {order_id} because it is already {current_status}."}
        if current_status == "cancelled":
             return {"ok": False, "error": f"Order {order_id} is already cancelled."}

        # Proceed to cancel
        update_query = "UPDATE orders SET status = 'Cancelled' WHERE order_id = %s"
        affected = execute(update_query, (order_id,))
        
        if affected == 0:
            return {"ok": False, "error": "Failed to cancel order. Please try again."}

    except DatabaseServiceError:
        return {"ok": False, "error": "Order service is temporarily unavailable."}

    if tool_context is not None:
        tool_context.state["last_order_id"] = order_id
        tool_context.state["last_intent"] = "order_cancellation"

    return {
        "ok": True,
        "message": f"Order {order_id} has been successfully cancelled."
    }