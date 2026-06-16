"""Product lookup tools backed by PostgreSQL."""

from __future__ import annotations

from typing import Any

from services.db import DatabaseServiceError
from services.repositories import ProductsRepository

try:
    from google.adk.tools import ToolContext  # type: ignore
    from google.adk.tools import tool  # type: ignore
except Exception:
    def tool(func):  # type: ignore
        return func

    class ToolContext:  # type: ignore
        state: dict[str, Any]


@tool
def lookup_product(product_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Lookup products by case-insensitive name match."""
    query = product_name.strip()
    if len(query) < 2:
        return {
            "ok": False,
            "error": "Product query is too short. Provide at least 2 characters.",
        }

    try:
        rows = ProductsRepository.lookup_products_by_name(query, limit=5)
    except DatabaseServiceError:
        return {"ok": False, "error": "Product service is temporarily unavailable."}

    if not rows:
        return {
            "ok": False,
            "error": f"No products found for '{query}'.",
            "query": query,
        }

    if tool_context is not None:
        tool_context.state["current_product_id"] = rows[0].get("product_id")
        tool_context.state["last_lookup_key"] = query
        tool_context.state["last_intent"] = "product_lookup"

    return {
        "ok": True,
        "query": query,
        "results": rows,
    }