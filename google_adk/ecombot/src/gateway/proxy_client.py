"""LiteLLM Gateway proxy client for eComBot.

Provides :class:`GatewayClient` — a thin wrapper around LiteLLM that
honours route hints, handles fallback on failure, and logs every
routing decision for observability.

Usage (inside the agent layer)::

    from gateway.proxy_client import create_gateway_model

    model = create_gateway_model()        # returns a configured LiteLlm
    agent = LlmAgent(model=model, ...)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from google.adk.models.lite_llm import LiteLlm

from config.settings import (
    LITELLM_PROXY_URL,
    LITELLM_PROXY_API_KEY,
    LITELLM_FAST_MODEL,
    LITELLM_DEEP_MODEL,
    LITELLM_FALLBACK_ENABLED,
    LITELLM_MAX_RETRIES,
    LITELLM_TIMEOUT_SECONDS,
)
from gateway.router import RouteDecision

logger = logging.getLogger(__name__)


# -----------------------
# Gateway Client
# -----------------------

@dataclass
class GatewayClient:
    """Wraps LiteLLM calls with routing metadata and fallback logic.

    Parameters
    ----------
    proxy_url:
        Base URL of the LiteLLM proxy (e.g. ``http://localhost:4000``).
    api_key:
        Optional key the proxy expects in the ``Authorization`` header.
    default_model:
        Model-group used when no route hint is supplied.
    fallback_model:
        Model-group used when the primary route fails.
    fallback_enabled:
        Whether automatic fallback is active.
    max_retries:
        Number of retries before declaring failure.
    timeout:
        Per-request timeout in seconds.
    """

    proxy_url: str = LITELLM_PROXY_URL
    api_key: str = LITELLM_PROXY_API_KEY
    default_model: str = LITELLM_FAST_MODEL
    fallback_model: str = LITELLM_DEEP_MODEL
    fallback_enabled: bool = LITELLM_FALLBACK_ENABLED
    max_retries: int = LITELLM_MAX_RETRIES
    timeout: float = LITELLM_TIMEOUT_SECONDS

    # internal bookkeeping
    _route_log: list[dict] = field(default_factory=list, repr=False)

    # -----------------------------------------------------------------
    # Public helpers
    # -----------------------------------------------------------------

    def resolve_model(self, decision: RouteDecision | None = None) -> str:
        """Return the model-group name to use for a given route decision."""
        model = decision.route_hint if decision else self.default_model
        logger.info(
            "GatewayClient.resolve_model → %s (confidence=%.2f, reason=%s)",
            model,
            decision.confidence if decision else 1.0,
            decision.reasoning if decision else "no decision provided",
        )
        self._log_route(model, decision)
        return model

    def fallback_model_for(self, decision: RouteDecision | None = None) -> str | None:
        """Return the fallback model group, or ``None`` if fallback is off."""
        if not self.fallback_enabled:
            return None
        if decision and decision.fallback_route:
            return decision.fallback_route
        return self.fallback_model

    def build_litellm_model(
        self,
        model_name: str | None = None,
    ) -> LiteLlm:
        """Create a :class:`LiteLlm` instance pointing at the proxy.

        Parameters
        ----------
        model_name:
            Explicit model-group name.  Falls back to *default_model*.
        """
        name = model_name or self.default_model
        return LiteLlm(
            model=name,
            api_key=self.api_key or None,
            api_base=self.proxy_url,
        )

    @property
    def route_log(self) -> list[dict]:
        """Read-only access to the route decision log."""
        return list(self._route_log)

    # -----------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------

    def _log_route(
        self,
        model: str,
        decision: RouteDecision | None,
    ) -> None:
        entry = {
            "model": model,
            "confidence": decision.confidence if decision else None,
            "reasoning": decision.reasoning if decision else None,
            "fallback": self.fallback_model_for(decision),
        }
        self._route_log.append(entry)
        logger.debug("Route log entry: %s", entry)


# -----------------------
# Factory function
# -----------------------

def create_gateway_model(
    route_decision: RouteDecision | None = None,
) -> LiteLlm:
    """Convenience factory: build a proxy-backed :class:`LiteLlm`.

    If *route_decision* is supplied, the model-group is chosen from
    its ``route_hint``; otherwise the default model (``fast-faq``) is
    used.
    """
    client = GatewayClient()
    model_name = client.resolve_model(route_decision)
    return client.build_litellm_model(model_name)
