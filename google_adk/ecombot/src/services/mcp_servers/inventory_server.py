"""FastMCP server exposing inventory / stock tools."""

from __future__ import annotations

import copy
import re
from typing import Any

from fastmcp import FastMCP

from services.mcp_servers.mock_data import INVENTORY

mcp = FastMCP("ecombot-inventory", host="127.0.0.1", port=8002)

_PRODUCT_ID_RE = re.compile(r"^PRD-\d{3}$")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _validate_product_id(product_id: str) -> dict[str, Any] | None:
    """Return an error dict if *product_id* is invalid, else ``None``."""
    if not _PRODUCT_ID_RE.fullmatch(product_id):
        return {"ok": False, "error": "Invalid product ID format. Expected format: PRD-XXX"}
    return None


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------

@mcp.tool()
async def check_stock(product_id: str) -> dict[str, Any]:
    """Check current stock level and availability for a product."""

    err = _validate_product_id(product_id)
    if err:
        return err

    product = INVENTORY.get(product_id)
    if not product:
        return {"ok": False, "error": f"Product {product_id} not found."}

    if product.get("discontinued"):
        return {
            "ok": False,
            "error": f"Product {product_id} ({product['name']}) has been discontinued.",
        }

    result: dict[str, Any] = {
        "product_id": product["product_id"],
        "name": product["name"],
        "total_stock": product["total_stock"],
        "available": product["available"],
        "reserved": product["reserved"],
        "in_stock": product["available"] > 0,
    }

    if "restock_date" in product:
        result["restock_date"] = product["restock_date"]

    return {"ok": True, "results": result}


@mcp.tool()
async def list_variants(product_id: str) -> dict[str, Any]:
    """List available variants (colours, switches, mounts, etc.) for a product."""

    err = _validate_product_id(product_id)
    if err:
        return err

    product = INVENTORY.get(product_id)
    if not product:
        return {"ok": False, "error": f"Product {product_id} not found."}

    if product.get("discontinued"):
        return {
            "ok": False,
            "error": f"Product {product_id} ({product['name']}) has been discontinued.",
        }

    variants = product.get("variants", [])
    if not variants:
        return {
            "ok": True,
            "results": {
                "product_id": product["product_id"],
                "name": product["name"],
                "variants": [],
                "note": "No variant information available for this product.",
            },
        }

    return {
        "ok": True,
        "results": {
            "product_id": product["product_id"],
            "name": product["name"],
            "variants": copy.deepcopy(variants),
        },
    }


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
