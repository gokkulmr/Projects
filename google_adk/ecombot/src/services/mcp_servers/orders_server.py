"""FastMCP server exposing order-management tools."""

from __future__ import annotations

import asyncio
import copy
import re
from typing import Any

from fastmcp import FastMCP

from services.mcp_servers.mock_data import (
    ORDERS,
    SIMULATE_ERROR_ORDER_ID,
    SIMULATE_TIMEOUT_ORDER_ID,
)

mcp = FastMCP("ecombot-orders", host="127.0.0.1", port=8001)

_ORDER_ID_RE = re.compile(r"^ORD-\d{3}$")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _validate_order_id(order_id: str) -> dict[str, Any] | None:
    """Return an error dict if *order_id* is invalid, else ``None``."""
    if not _ORDER_ID_RE.fullmatch(order_id):
        return {"ok": False, "error": "Invalid order ID format. Expected format: ORD-XXX"}
    return None


async def _handle_special_ids(order_id: str) -> dict[str, Any] | None:
    """Simulate timeout / internal error for special IDs."""
    if order_id == SIMULATE_TIMEOUT_ORDER_ID:
        await asyncio.sleep(30)  # long enough to trigger client timeout
        return {"ok": False, "error": "Request timed out."}
    if order_id == SIMULATE_ERROR_ORDER_ID:
        return {"ok": False, "error": "Internal server error."}
    return None


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------

@mcp.tool()
async def get_order_status(order_id: str) -> dict[str, Any]:
    """Retrieve the current status and key details of an order."""

    err = _validate_order_id(order_id)
    if err:
        return err

    special = await _handle_special_ids(order_id)
    if special:
        return special

    order = ORDERS.get(order_id)
    if not order:
        return {"ok": False, "error": f"Order {order_id} not found."}

    return {
        "ok": True,
        "results": {
            "order_id": order["order_id"],
            "customer_name": order["customer_name"],
            "status": order["status"],
            "product_name": order["product_name"],
            "quantity": order["quantity"],
            "created_at": order["created_at"],
        },
    }


@mcp.tool()
async def get_order_details(order_id: str) -> dict[str, Any]:
    """Retrieve full item-level details including shipping information."""

    err = _validate_order_id(order_id)
    if err:
        return err

    special = await _handle_special_ids(order_id)
    if special:
        return special

    order = ORDERS.get(order_id)
    if not order:
        return {"ok": False, "error": f"Order {order_id} not found."}

    return {"ok": True, "results": copy.deepcopy(order)}


@mcp.tool()
async def cancel_order(order_id: str, reason: str = "Customer requested") -> dict[str, Any]:
    """Cancel an order if it has not shipped yet.

    Only orders in ``processing`` status can be cancelled.
    """

    err = _validate_order_id(order_id)
    if err:
        return err

    special = await _handle_special_ids(order_id)
    if special:
        return special

    order = ORDERS.get(order_id)
    if not order:
        return {"ok": False, "error": f"Order {order_id} not found."}

    status = order["status"].lower()
    if status == "cancelled":
        return {"ok": False, "error": f"Order {order_id} is already cancelled."}
    if status in {"shipped", "delivered"}:
        return {
            "ok": False,
            "error": f"Cannot cancel order {order_id} because it is already {status}.",
        }
    if status != "processing":
        return {
            "ok": False,
            "error": f"Cannot cancel order {order_id} with status '{status}'.",
        }

    # Mutate the in-memory record so repeated calls reflect the change
    order["status"] = "cancelled"
    order["cancellation_reason"] = reason

    return {"ok": True, "message": f"Order {order_id} has been successfully cancelled."}


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
