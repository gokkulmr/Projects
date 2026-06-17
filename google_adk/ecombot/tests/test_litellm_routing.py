"""Unit tests for LiteLLM Gateway routing and proxy client.

Run with:  pytest tests/test_litellm_routing.py -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# ── Ensure ``src/`` is on the import path ────────────────────────────
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"),
)


# =====================================================================
# Router tests
# =====================================================================

class TestClassifyQuery:
    """Verify the heuristic query classifier."""

    # We import inside the class to guarantee sys.path is set.
    @staticmethod
    def _classify(text: str):
        from gateway.router import classify_query
        return classify_query(text)

    # ── Simple / fast-faq queries ─────────────────────────────────

    @pytest.mark.parametrize(
        "query",
        [
            "Where is my order?",
            "What is the return policy?",
            "Is the keyboard in stock?",
            "Track my order ORD-123",
            "What payment methods do you accept?",
            "How can I cancel my order?",
            "Hi",
            "Thanks!",
            "What is the price of headphones?",
            "Shipping cost?",
        ],
    )
    def test_simple_queries_route_to_fast(self, query: str):
        decision = self._classify(query)
        assert decision.route_hint == "fast-faq", (
            f"Expected fast-faq for '{query}', got {decision.route_hint} "
            f"({decision.reasoning})"
        )

    # ── Complex / deep-support queries ────────────────────────────

    @pytest.mark.parametrize(
        "query",
        [
            "Compare the Wireless Headphones vs the Mechanical Keyboard",
            "I am very frustrated with my damaged order, this is the third "
            "time this has happened and I want to escalate this complaint",
            "Can you recommend something better than the USB-C hub? "
            "I need multiple ports and a custom setup for my workstation",
            "Why was my item missing from the delivery? I received the "
            "wrong item and I want a full refund plus compensation for "
            "the inconvenience. Please explain the next steps.",
        ],
    )
    def test_complex_queries_route_to_deep(self, query: str):
        decision = self._classify(query)
        assert decision.route_hint == "deep-support", (
            f"Expected deep-support for '{query[:50]}…', got "
            f"{decision.route_hint} ({decision.reasoning})"
        )

    # ── Edge cases ────────────────────────────────────────────────

    def test_empty_input_defaults_to_fast(self):
        decision = self._classify("")
        assert decision.route_hint == "fast-faq"
        assert decision.confidence == 1.0

    def test_decision_has_fallback_route(self):
        decision = self._classify("Where is my order?")
        assert decision.fallback_route != ""

    def test_confidence_in_range(self):
        for q in ["Hi", "Compare X vs Y in detail please explain why"]:
            decision = self._classify(q)
            assert 0.0 <= decision.confidence <= 1.0


# =====================================================================
# GatewayClient tests
# =====================================================================

class TestGatewayClient:
    """Verify the GatewayClient wrapper (no live proxy needed)."""

    @staticmethod
    def _make_client(**overrides):
        from gateway.proxy_client import GatewayClient
        defaults = dict(
            proxy_url="http://localhost:4000",
            api_key="test-key",
            default_model="fast-faq",
            fallback_model="deep-support",
            fallback_enabled=True,
            max_retries=2,
            timeout=30.0,
        )
        defaults.update(overrides)
        return GatewayClient(**defaults)

    @staticmethod
    def _make_decision(route: str = "fast-faq", confidence: float = 0.9):
        from gateway.router import RouteDecision
        return RouteDecision(
            route_hint=route,
            confidence=confidence,
            reasoning="test",
            fallback_route="deep-support" if route == "fast-faq" else "fast-faq",
        )

    # ── resolve_model ─────────────────────────────────────────────

    def test_resolve_model_uses_decision_hint(self):
        client = self._make_client()
        decision = self._make_decision("deep-support")
        assert client.resolve_model(decision) == "deep-support"

    def test_resolve_model_defaults_when_no_decision(self):
        client = self._make_client()
        assert client.resolve_model(None) == "fast-faq"

    # ── fallback ──────────────────────────────────────────────────

    def test_fallback_returns_model_when_enabled(self):
        client = self._make_client(fallback_enabled=True)
        decision = self._make_decision("fast-faq")
        assert client.fallback_model_for(decision) == "deep-support"

    def test_fallback_returns_none_when_disabled(self):
        client = self._make_client(fallback_enabled=False)
        decision = self._make_decision("fast-faq")
        assert client.fallback_model_for(decision) is None

    # ── build_litellm_model ───────────────────────────────────────

    def test_build_litellm_model_returns_litellm_instance(self):
        client = self._make_client()
        model = client.build_litellm_model("fast-faq")
        assert model is not None
        # LiteLlm stores the model string internally
        assert model._model == "fast-faq"

    def test_build_litellm_model_uses_proxy_url(self):
        client = self._make_client(proxy_url="http://my-proxy:9000")
        model = client.build_litellm_model("deep-support")
        assert model._api_base == "http://my-proxy:9000"

    # ── route log ─────────────────────────────────────────────────

    def test_route_log_records_entries(self):
        client = self._make_client()
        decision = self._make_decision("fast-faq", 0.85)
        client.resolve_model(decision)
        client.resolve_model(None)

        log = client.route_log
        assert len(log) == 2
        assert log[0]["model"] == "fast-faq"
        assert log[0]["confidence"] == 0.85
        assert log[1]["model"] == "fast-faq"  # default
        assert log[1]["confidence"] is None


# =====================================================================
# Config tests
# =====================================================================

class TestGatewayConfig:
    """Verify the gateway settings load from config."""

    def test_default_values(self):
        from config.settings import (
            LITELLM_PROXY_ENABLED,
            LITELLM_PROXY_URL,
            LITELLM_FAST_MODEL,
            LITELLM_DEEP_MODEL,
            LITELLM_FALLBACK_ENABLED,
            LITELLM_MAX_RETRIES,
            LITELLM_TIMEOUT_SECONDS,
        )
        # Proxy is off by default
        assert LITELLM_PROXY_ENABLED is False
        assert LITELLM_PROXY_URL == "http://localhost:4000"
        assert LITELLM_FAST_MODEL == "fast-faq"
        assert LITELLM_DEEP_MODEL == "deep-support"
        assert LITELLM_FALLBACK_ENABLED is True
        assert LITELLM_MAX_RETRIES == 2
        assert LITELLM_TIMEOUT_SECONDS == 30.0


# =====================================================================
# create_gateway_model factory tests
# =====================================================================

class TestCreateGatewayModel:
    """Verify the convenience factory function."""

    def test_factory_without_decision(self):
        from gateway.proxy_client import create_gateway_model
        model = create_gateway_model()
        assert model._model == "fast-faq"

    def test_factory_with_decision(self):
        from gateway.proxy_client import create_gateway_model
        from gateway.router import RouteDecision

        decision = RouteDecision(
            route_hint="deep-support",
            confidence=0.92,
            reasoning="unit test",
            fallback_route="fast-faq",
        )
        model = create_gateway_model(decision)
        assert model._model == "deep-support"
