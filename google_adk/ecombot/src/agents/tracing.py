"""Orchestration tracing for multi-agent delegation decisions."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TraceEntry:
    """Single orchestration trace record."""
    timestamp: float
    user_message: str
    routing_decision: str  # 'support', 'sales', 'self', 'mixed'
    reasoning: str
    agent_called: str
    response_summary: str = ""
    duration_ms: float = 0.0


class OrchestrationTracer:
    """Records delegation decisions for debugging and observability."""

    def __init__(self) -> None:
        self._traces: list[TraceEntry] = []

    def start_trace(
        self,
        user_message: str,
        routing_decision: str,
        reasoning: str,
        agent_called: str,
    ) -> TraceEntry:
        entry = TraceEntry(
            timestamp=time.time(),
            user_message=user_message,
            routing_decision=routing_decision,
            reasoning=reasoning,
            agent_called=agent_called,
        )
        self._traces.append(entry)
        logger.info(
            "[TRACE] %s → %s (%s): %s",
            routing_decision,
            agent_called,
            reasoning,
            user_message[:80],
        )
        return entry

    def end_trace(self, entry: TraceEntry, response: str) -> None:
        entry.duration_ms = (time.time() - entry.timestamp) * 1000
        entry.response_summary = response[:200]
        logger.info(
            "[TRACE] %s completed in %.0fms",
            entry.agent_called,
            entry.duration_ms,
        )

    @property
    def traces(self) -> list[TraceEntry]:
        return list(self._traces)

    def print_report(self) -> None:
        print("\n" + "=" * 60)
        print(" ORCHESTRATION TRACE REPORT")
        print("=" * 60)
        for i, t in enumerate(self._traces, 1):
            print(f"\n--- Turn {i} ---")
            print(f"  User:     {t.user_message[:80]}")
            print(f"  Decision: {t.routing_decision}")
            print(f"  Agent:    {t.agent_called}")
            print(f"  Reason:   {t.reasoning}")
            print(f"  Duration: {t.duration_ms:.0f}ms")
            print(f"  Response: {t.response_summary[:100]}...")
        print("\n" + "=" * 60)
