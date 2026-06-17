"""MCP client wrapper – calls FastMCP order & inventory servers over HTTP."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Errors
# ------------------------------------------------------------------

class MCPClientError(Exception):
    """Base error for MCP client operations."""


class MCPTimeoutError(MCPClientError):
    """Raised when an MCP server does not respond in time."""


class MCPServerError(MCPClientError):
    """Raised when the MCP server returns a non-200 response."""


# ------------------------------------------------------------------
# Client wrapper
# ------------------------------------------------------------------

class MCPClientWrapper:
    """Thin HTTP wrapper around the FastMCP servers.

    Each public method sends a JSON-RPC–style request to the relevant
    MCP server and returns the parsed result dict.
    """

    def __init__(
        self,
        orders_base_url: str | None = None,
        inventory_base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._orders_url = orders_base_url or (
            f"http://{settings.MCP_ORDERS_HOST}:{settings.MCP_ORDERS_PORT}"
        )
        self._inventory_url = inventory_base_url or (
            f"http://{settings.MCP_INVENTORY_HOST}:{settings.MCP_INVENTORY_PORT}"
        )
        self._timeout = timeout or settings.MCP_TIMEOUT_SECONDS

    # ---- internal helpers -----------------------------------------

    async def _call(self, base_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute one MCP tool call over HTTP and return the result."""
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
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            logger.warning("MCP timeout for %s/%s: %s", base_url, tool_name, exc)
            raise MCPTimeoutError(f"MCP server timed out calling {tool_name}") from exc
        except httpx.HTTPError as exc:
            logger.error("MCP HTTP error for %s/%s: %s", base_url, tool_name, exc)
            raise MCPServerError(f"MCP server error calling {tool_name}: {exc}") from exc

        if resp.status_code != 200:
            logger.error("MCP non-200 for %s/%s: %s %s", base_url, tool_name, resp.status_code, resp.text)
            raise MCPServerError(
                f"MCP server returned {resp.status_code} for {tool_name}"
            )

        data = resp.json()
        logger.info("MCP reply ← %s/%s  result=%s", base_url, tool_name, data)
        return data  # type: ignore[return-value]

    # ---- order tools ----------------------------------------------

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Call *get_order_status* on the orders MCP server."""
        return await self._call(self._orders_url, "get_order_status", {"order_id": order_id})

    async def get_order_details(self, order_id: str) -> dict[str, Any]:
        """Call *get_order_details* on the orders MCP server."""
        return await self._call(self._orders_url, "get_order_details", {"order_id": order_id})

    async def cancel_order(self, order_id: str, reason: str = "Customer requested") -> dict[str, Any]:
        """Call *cancel_order* on the orders MCP server."""
        return await self._call(self._orders_url, "cancel_order", {"order_id": order_id, "reason": reason})

    # ---- inventory tools ------------------------------------------

    async def check_stock(self, product_id: str) -> dict[str, Any]:
        """Call *check_stock* on the inventory MCP server."""
        return await self._call(self._inventory_url, "check_stock", {"product_id": product_id})

    async def list_variants(self, product_id: str) -> dict[str, Any]:
        """Call *list_variants* on the inventory MCP server."""
        return await self._call(self._inventory_url, "list_variants", {"product_id": product_id})


# ------------------------------------------------------------------
# User-friendly error messages
# ------------------------------------------------------------------

def friendly_error(exc: Exception) -> dict[str, Any]:
    """Convert an MCPClientError into a user-friendly response dict."""
    if isinstance(exc, MCPTimeoutError):
        return {
            "ok": False,
            "error": "The service is taking too long to respond. Please try again shortly.",
        }
    if isinstance(exc, MCPServerError):
        return {
            "ok": False,
            "error": "The service is temporarily unavailable. Please try again later.",
        }
    return {
        "ok": False,
        "error": f"An unexpected error occurred: {exc}",
    }


# ------------------------------------------------------------------
# Factory – returns ADK-compatible tool functions
# ------------------------------------------------------------------

_client: MCPClientWrapper | None = None


def _get_client() -> MCPClientWrapper:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = MCPClientWrapper()
    return _client


def create_mcp_tools() -> list:
    """Return a list of ADK-compatible tool functions backed by the MCP servers.

    Imports are deferred so that this module can be loaded even when
    ``google-adk`` is not installed (e.g. during unit testing).
    """
    from tools.mcp_order_tools import (
        mcp_cancel_order,
        mcp_check_stock,
        mcp_get_order_status,
        mcp_list_variants,
    )

    return [mcp_get_order_status, mcp_cancel_order, mcp_check_stock, mcp_list_variants]
