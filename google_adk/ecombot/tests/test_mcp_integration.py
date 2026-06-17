"""Unit tests for MCP mock data and server tool logic.

These tests exercise the tool functions directly (in-process) so that
no running FastMCP server is required.
"""

from __future__ import annotations

import asyncio
import sys
import os

import pytest

# Ensure the src directory is on sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.mcp_servers.mock_data import (
    INVENTORY,
    ORDERS,
    SIMULATE_ERROR_ORDER_ID,
    SIMULATE_TIMEOUT_ORDER_ID,
)
from services.mcp_servers.orders_server import (
    cancel_order,
    get_order_details,
    get_order_status,
)
from services.mcp_servers.inventory_server import (
    check_stock,
    list_variants,
)


# ==================================================================
# Mock-data consistency
# ==================================================================

class TestMockDataConsistency:
    """Verify that ORDERS and INVENTORY mock data are internally consistent."""

    def test_all_order_product_ids_exist_in_inventory(self):
        for oid, order in ORDERS.items():
            pid = order["product_id"]
            assert pid in INVENTORY, f"Order {oid} references unknown product {pid}"

    def test_order_ids_match_keys(self):
        for key, order in ORDERS.items():
            assert key == order["order_id"]

    def test_inventory_ids_match_keys(self):
        for key, product in INVENTORY.items():
            assert key == product["product_id"]

    def test_orders_have_required_fields(self):
        required = {"order_id", "customer_name", "status", "product_id", "product_name", "quantity", "created_at"}
        for oid, order in ORDERS.items():
            missing = required - set(order.keys())
            assert not missing, f"Order {oid} missing fields: {missing}"

    def test_inventory_have_required_fields(self):
        required = {"product_id", "name", "total_stock", "available", "reserved"}
        for pid, product in INVENTORY.items():
            missing = required - set(product.keys())
            assert not missing, f"Product {pid} missing fields: {missing}"


# ==================================================================
# Order server tools
# ==================================================================

class TestGetOrderStatus:
    """Tests for the get_order_status tool."""

    def test_valid_order(self):
        result = asyncio.run(get_order_status("ORD-001"))
        assert result["ok"] is True
        assert result["results"]["order_id"] == "ORD-001"
        assert result["results"]["status"] == "shipped"

    def test_invalid_format(self):
        result = asyncio.run(get_order_status("INVALID"))
        assert result["ok"] is False
        assert "Invalid order ID format" in result["error"]

    def test_not_found(self):
        result = asyncio.run(get_order_status("ORD-777"))
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_error_simulation(self):
        result = asyncio.run(get_order_status(SIMULATE_ERROR_ORDER_ID))
        assert result["ok"] is False
        assert "Internal server error" in result["error"]


class TestGetOrderDetails:
    """Tests for the get_order_details tool."""

    def test_valid_order_full_details(self):
        result = asyncio.run(get_order_details("ORD-001"))
        assert result["ok"] is True
        details = result["results"]
        assert details["shipping_carrier"] == "BlueDart"
        assert details["tracking_number"] == "BD1234567890"

    def test_delivered_order(self):
        result = asyncio.run(get_order_details("ORD-002"))
        assert result["ok"] is True
        assert result["results"]["status"] == "delivered"
        assert "delivered_at" in result["results"]

    def test_not_found(self):
        result = asyncio.run(get_order_details("ORD-777"))
        assert result["ok"] is False


class TestCancelOrder:
    """Tests for the cancel_order tool."""

    def test_cancel_processing_order(self):
        # ORD-004 starts as "processing"
        # Reset state first
        ORDERS["ORD-004"]["status"] = "processing"
        ORDERS["ORD-004"].pop("cancellation_reason", None)

        result = asyncio.run(cancel_order("ORD-004"))
        assert result["ok"] is True
        assert "successfully cancelled" in result["message"]

        # Reset for other tests
        ORDERS["ORD-004"]["status"] = "processing"
        ORDERS["ORD-004"].pop("cancellation_reason", None)

    def test_cancel_shipped_order(self):
        result = asyncio.run(cancel_order("ORD-001"))
        assert result["ok"] is False
        assert "already shipped" in result["error"]

    def test_cancel_delivered_order(self):
        result = asyncio.run(cancel_order("ORD-002"))
        assert result["ok"] is False
        assert "already delivered" in result["error"]

    def test_cancel_already_cancelled(self):
        result = asyncio.run(cancel_order("ORD-003"))
        assert result["ok"] is False
        assert "already cancelled" in result["error"]

    def test_cancel_with_reason(self):
        ORDERS["ORD-004"]["status"] = "processing"
        ORDERS["ORD-004"].pop("cancellation_reason", None)

        result = asyncio.run(cancel_order("ORD-004", reason="Found a better deal"))
        assert result["ok"] is True

        # Reset for other tests
        ORDERS["ORD-004"]["status"] = "processing"
        ORDERS["ORD-004"].pop("cancellation_reason", None)

    def test_cancel_invalid_format(self):
        result = asyncio.run(cancel_order("bad-id"))
        assert result["ok"] is False
        assert "Invalid order ID format" in result["error"]


# ==================================================================
# Inventory server tools
# ==================================================================

class TestCheckStock:
    """Tests for the check_stock tool."""

    def test_in_stock_product(self):
        result = asyncio.run(check_stock("PRD-101"))
        assert result["ok"] is True
        assert result["results"]["available"] == 47
        assert result["results"]["in_stock"] is True

    def test_out_of_stock_product(self):
        result = asyncio.run(check_stock("PRD-102"))
        assert result["ok"] is True
        assert result["results"]["available"] == 0
        assert result["results"]["in_stock"] is False
        assert "restock_date" in result["results"]

    def test_discontinued_product(self):
        result = asyncio.run(check_stock("PRD-105"))
        assert result["ok"] is False
        assert "discontinued" in result["error"]

    def test_invalid_format(self):
        result = asyncio.run(check_stock("INVALID"))
        assert result["ok"] is False
        assert "Invalid product ID format" in result["error"]

    def test_not_found(self):
        result = asyncio.run(check_stock("PRD-999"))
        assert result["ok"] is False
        assert "not found" in result["error"]


class TestListVariants:
    """Tests for the list_variants tool."""

    def test_variants_with_colors(self):
        result = asyncio.run(list_variants("PRD-101"))
        assert result["ok"] is True
        variants = result["results"]["variants"]
        assert len(variants) == 3
        assert variants[0]["color"] == "Black"

    def test_variants_with_switches(self):
        result = asyncio.run(list_variants("PRD-102"))
        assert result["ok"] is True
        variants = result["results"]["variants"]
        assert any(v.get("switch") == "Red" for v in variants)

    def test_discontinued_product(self):
        result = asyncio.run(list_variants("PRD-105"))
        assert result["ok"] is False
        assert "discontinued" in result["error"]

    def test_not_found(self):
        result = asyncio.run(list_variants("PRD-999"))
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_invalid_format(self):
        result = asyncio.run(list_variants("bad"))
        assert result["ok"] is False
        assert "Invalid product ID format" in result["error"]


# ==================================================================
# Timeout simulation (order server)
# ==================================================================

class TestTimeoutSimulation:
    """Verify that the timeout-simulation ID blocks as expected."""

    def test_timeout_order_id_sleeps(self):
        """The tool should take >2 s when called with the timeout ID.

        We cancel the coroutine early to avoid waiting the full 30 s
        in CI.
        """
        async def _run():
            task = asyncio.create_task(get_order_status(SIMULATE_TIMEOUT_ORDER_ID))
            await asyncio.sleep(0.1)  # give the task a moment
            assert not task.done(), "Expected the timeout simulation to still be running"
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(_run())
