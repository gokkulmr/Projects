"""ADK-compatible tool wrappers that delegate to FastMCP servers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config import settings

try:
    from google.adk.tools import ToolContext  # type: ignore
    from google.adk.tools import tool  # type: ignore
except Exception:
    def tool(func):  # type: ignore
        return func

    class ToolContext:  # type: ignore
        state: dict[str, Any]


logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

_ORDERS_URL: str | None = None
_INVENTORY_URL: str | None = None


def _orders_url() -> str:
    global _ORDERS_URL  # noqa: PLW0603
    if _ORDERS_URL is None:
        _ORDERS_URL = f"http://{settings.MCP_ORDERS_HOST}:{settings.MCP_ORDERS_PORT}"
    return _ORDERS_URL


def _inventory_url() -> str:
    global _INVENTORY_URL  # noqa: PLW0603
    if _INVENTORY_URL is None:
        _INVENTORY_URL = f"http://{settings.MCP_INVENTORY_HOST}:{settings.MCP_INVENTORY_PORT}"
    return _INVENTORY_URL


async def _mcp_call(base_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Send a JSON-RPC tools/call request to a FastMCP server."""
    url = f"{base_url}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    logger.info("MCP call  → %s/%s  args=%s", base_url, tool_name, arguments)
    try:
        async with httpx.AsyncClient(timeout=settings.MCP_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        logger.info("MCP reply ← %s/%s  result=%s", base_url, tool_name, data)
        return data  # type: ignore[return-value]
    except httpx.TimeoutException:
        logger.warning("MCP timeout for %s/%s", base_url, tool_name)
        return {"ok": False, "error": "The service is taking too long to respond. Please try again shortly."}
    except httpx.HTTPError as exc:
        logger.error("MCP HTTP error for %s/%s: %s", base_url, tool_name, exc)
        return {"ok": False, "error": "The service is temporarily unavailable. Please try again later."}


def _sync_mcp_call(base_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run the async MCP call in the current or a new event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We are already inside an async context (e.g. ADK handler).
        # Create a new thread to avoid blocking the loop.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _mcp_call(base_url, tool_name, arguments))
            return future.result(timeout=settings.MCP_TIMEOUT_SECONDS + 5)
    else:
        return asyncio.run(_mcp_call(base_url, tool_name, arguments))


# ------------------------------------------------------------------
# ADK tools
# ------------------------------------------------------------------

@tool
def mcp_get_order_status(order_id: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Get order status via MCP orders server."""
    result = _sync_mcp_call(_orders_url(), "get_order_status", {"order_id": order_id})

    if tool_context is not None:
        tool_context.state["last_order_id"] = order_id
        tool_context.state["last_intent"] = "order_lookup"

    return result


@tool
def mcp_cancel_order(
    order_id: str,
    reason: str = "Customer requested",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Cancel an order via MCP orders server."""
    result = _sync_mcp_call(_orders_url(), "cancel_order", {"order_id": order_id, "reason": reason})

    if tool_context is not None:
        tool_context.state["last_order_id"] = order_id
        tool_context.state["last_intent"] = "order_cancellation"

    return result


@tool
def mcp_check_stock(product_id: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Check product stock via MCP inventory server."""
    result = _sync_mcp_call(_inventory_url(), "check_stock", {"product_id": product_id})

    if tool_context is not None:
        tool_context.state["current_product_id"] = product_id
        tool_context.state["last_intent"] = "stock_check"

    return result


@tool
def mcp_list_variants(product_id: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """List product variants via MCP inventory server."""
    result = _sync_mcp_call(_inventory_url(), "list_variants", {"product_id": product_id})

    if tool_context is not None:
        tool_context.state["current_product_id"] = product_id
        tool_context.state["last_intent"] = "variant_lookup"

    return result
