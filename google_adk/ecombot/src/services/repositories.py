"""Repository helpers to keep SQL out of tool code."""

from __future__ import annotations

from typing import Any

from .db import execute
from .db import fetch_all
from .db import fetch_one


class OrdersRepository:
    """Data access for order operations."""

    @staticmethod
    def get_order_by_id(order_id: str) -> dict[str, Any] | None:
        return fetch_one(
            """
            SELECT
                order_id,
                customer_name,
                status,
                eta,
                carrier,
                tracking_number,
                total_amount,
                currency,
                updated_at
            FROM orders
            WHERE order_id = %s
            """,
            (order_id,),
        )

    @staticmethod
    def cancel_order(order_id: str) -> bool:
        updated = execute(
            """
            UPDATE orders
            SET status = 'Cancelled',
                eta = NULL,
                updated_at = NOW()
            WHERE order_id = %s
              AND status NOT IN ('Cancelled', 'Delivered')
            """,
            (order_id,),
        )
        return updated > 0


class ProductsRepository:
    """Data access for product operations."""

    @staticmethod
    def lookup_products_by_name(product_name: str, limit: int = 5) -> list[dict[str, Any]]:
        pattern = f"%{product_name}%"
        return fetch_all(
            """
            SELECT
                product_id,
                product_name,
                category,
                price,
                currency,
                in_stock,
                inventory_count,
                is_active,
                rating,
                tags
            FROM products
            WHERE product_name ILIKE %s
            ORDER BY is_active DESC, in_stock DESC, rating DESC NULLS LAST, product_name ASC
            LIMIT %s
            """,
            (pattern, limit),
        )