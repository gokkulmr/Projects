"""Conversation history persistence in PostgreSQL."""

from __future__ import annotations

import json
from typing import Any

from psycopg.types.json import Json

from services.db import execute
from services.db import fetch_all


class HistoryService:
    """Store and retrieve chat turns for debugging and replay."""

    def save_turn(
        self,
        *,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        execute(
            """
            INSERT INTO session_history (session_id, user_id, role, content, tool_calls)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session_id,
                user_id,
                role,
                content,
                Json(tool_calls) if tool_calls is not None else None,
            ),
        )

    def get_conversation(self, *, session_id: str) -> list[dict[str, Any]]:
        return fetch_all(
            """
            SELECT session_id, user_id, role, content, tool_calls, created_at
            FROM session_history
            WHERE session_id = %s
            ORDER BY created_at ASC, id ASC
            """,
            (session_id,),
        )

    def save_adk_event(
        self,
        *,
        session_id: str,
        user_id: str,
        author: str,
        content_parts: list[str],
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        has_tool_calls = bool(tool_calls)
        if author == "user":
            role = "user"
        elif has_tool_calls:
            role = "tool"
        else:
            role = "assistant"

        content = "\n".join(part for part in content_parts if part).strip()
        if not content and not has_tool_calls:
            return
        if not content:
            content = json.dumps(tool_calls or [], ensure_ascii=True)
        self.save_turn(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )