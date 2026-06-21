"""Structured card renderers for Chainlit UI."""

from __future__ import annotations
from typing import Any


def render_order_card(order: dict[str, Any]) -> str:
    """Render an order as a formatted markdown card."""
    status = order.get("status", "Unknown")
    status_emoji = {
        "processing": "🔄",
        "shipped": "📦",
        "delivered": "✅",
        "cancelled": "❌",
    }.get(status.lower(), "❓")

    lines = [
        f"### {status_emoji} Order {order.get('order_id', 'N/A')}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Customer** | {order.get('customer_name', 'N/A')} |",
        f"| **Status** | {status.title()} |",
        f"| **Product** | {order.get('product_name', order.get('product_id', 'N/A'))} |",
        f"| **Quantity** | {order.get('quantity', 'N/A')} |",
        f"| **Created** | {order.get('created_at', 'N/A')} |",
    ]

    if order.get("shipping_carrier"):
        lines.append(f"| **Carrier** | {order['shipping_carrier']} |")
    if order.get("tracking_number"):
        lines.append(f"| **Tracking** | {order['tracking_number']} |")
    if order.get("estimated_delivery"):
        lines.append(f"| **ETA** | {order['estimated_delivery']} |")

    return "\n".join(lines)


def render_product_card(product: dict[str, Any]) -> str:
    """Render a product as a formatted markdown card."""
    in_stock = product.get("stock", 0) > 0 if isinstance(product.get("stock"), (int, float)) else product.get("in_stock", False)
    stock_emoji = "🟢" if in_stock else "🔴"

    price = product.get("price")
    price_str = f"₹{price:,.2f}" if price else "N/A"

    lines = [
        f"### 🛍️ {product.get('name', 'Unknown Product')}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **ID** | {product.get('product_id', 'N/A')} |",
        f"| **Price** | {price_str} |",
        f"| **Stock** | {stock_emoji} {product.get('stock', 'N/A')} units |",
        f"| **Active** | {'Yes' if product.get('active', True) else 'Discontinued'} |",
    ]

    if product.get("description"):
        lines.append(f"| **Description** | {product['description']} |")

    return "\n".join(lines)


def render_stock_card(stock_info: dict[str, Any]) -> str:
    """Render stock information as a formatted markdown card."""
    in_stock = stock_info.get("in_stock", False)
    emoji = "🟢" if in_stock else "🔴"

    lines = [
        f"### {emoji} Stock: {stock_info.get('name', 'Unknown')}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Product ID** | {stock_info.get('product_id', 'N/A')} |",
        f"| **Available** | {stock_info.get('available', 0)} |",
        f"| **Reserved** | {stock_info.get('reserved', 0)} |",
        f"| **Total Stock** | {stock_info.get('total_stock', 0)} |",
    ]

    if stock_info.get("restock_date"):
        lines.append(f"| **Restock Date** | {stock_info['restock_date']} |")

    return "\n".join(lines)
