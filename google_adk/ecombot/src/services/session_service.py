"""Redis-backed ADK session service for durable short-lived context."""

from __future__ import annotations

import json
import logging
from typing import Any
from typing import Optional

import redis
from typing_extensions import override

from google.adk.events.event import Event
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.sessions.session import Session

from config.settings import REDIS_SESSION_TTL_SECONDS
from config.settings import redis_url
from services.history_service import HistoryService

logger = logging.getLogger(__name__)


class RedisBackedSessionService(BaseSessionService):
    """Persist ADK session state in Redis while keeping ADK-compatible behavior."""

    def __init__(self, ttl_seconds: int = REDIS_SESSION_TTL_SECONDS):
        self._memory = InMemorySessionService()
        self._ttl_seconds = ttl_seconds
        self._history = HistoryService()
        self._redis = redis.Redis.from_url(redis_url(), decode_responses=True)

    def _key(self, app_name: str, user_id: str, session_id: str) -> str:
        return f"adk:session:{app_name}:{user_id}:{session_id}"

    def _parse_key(self, key: str) -> tuple[str, str, str] | None:
        parts = key.split(":", 4)
        if len(parts) != 5:
            return None
        _, _, app_name, user_id, session_id = parts
        return app_name, user_id, session_id

    def _persist_state(self, session: Session) -> None:
        payload = {
            "app_name": session.app_name,
            "user_id": session.user_id,
            "session_id": session.id,
            "state": json.dumps(session.state, ensure_ascii=True),
            "last_update_time": str(session.last_update_time),
        }
        key = self._key(session.app_name, session.user_id, session.id)
        self._redis.hset(key, mapping=payload)
        self._redis.expire(key, self._ttl_seconds)

    def _load_state(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> dict[str, Any] | None:
        key = self._key(app_name, user_id, session_id)
        payload = self._redis.hgetall(key)
        if not payload:
            return None
        raw_state = payload.get("state", "{}")
        try:
            return json.loads(raw_state)
        except json.JSONDecodeError:
            logger.warning("Invalid Redis state for key %s", key)
            return {}

    def _event_content_parts(self, event: Event) -> list[str]:
        text_parts: list[str] = []
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    text_parts.append(part.text)
        return text_parts

    def _event_tool_calls(self, event: Event) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        for call in event.get_function_calls():
            calls.append(
                {
                    "type": "function_call",
                    "name": call.name,
                    "args": dict(call.args or {}),
                    "id": call.id,
                }
            )
        for response in event.get_function_responses():
            calls.append(
                {
                    "type": "function_response",
                    "name": response.name,
                    "response": dict(response.response or {}),
                    "id": response.id,
                }
            )
        return calls

    @override
    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        session = await self._memory.create_session(
            app_name=app_name,
            user_id=user_id,
            state=state,
            session_id=session_id,
        )
        try:
            self._persist_state(session)
        except redis.RedisError:
            logger.exception("Failed to persist session to Redis")
        return session

    @override
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        session = await self._memory.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )
        if session is not None:
            return session

        try:
            state = self._load_state(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except redis.RedisError:
            logger.exception("Failed to restore session from Redis")
            return None

        if state is None:
            return None

        await self._memory.create_session(
            app_name=app_name,
            user_id=user_id,
            state=state,
            session_id=session_id,
        )
        return await self._memory.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )

    @override
    async def list_sessions(
        self,
        *,
        app_name: str,
        user_id: Optional[str] = None,
    ) -> ListSessionsResponse:
        sessions = await self._memory.list_sessions(app_name=app_name, user_id=user_id)
        if sessions.sessions:
            return sessions

        try:
            pattern = f"adk:session:{app_name}:{user_id if user_id else '*'}:*"
            keys = self._redis.keys(pattern)
        except redis.RedisError:
            logger.exception("Failed to list sessions from Redis")
            return sessions

        restored: list[Session] = []
        for key in keys:
            parsed = self._parse_key(key)
            if parsed is None:
                continue
            parsed_app, parsed_user, parsed_session = parsed
            state = self._load_state(
                app_name=parsed_app,
                user_id=parsed_user,
                session_id=parsed_session,
            ) or {}
            restored.append(
                Session(
                    app_name=parsed_app,
                    user_id=parsed_user,
                    id=parsed_session,
                    state=state,
                    events=[],
                )
            )
        return ListSessionsResponse(sessions=restored)

    @override
    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        await self._memory.delete_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        try:
            self._redis.delete(self._key(app_name, user_id, session_id))
        except redis.RedisError:
            logger.exception("Failed to delete session from Redis")

    @override
    async def append_event(self, session: Session, event: Event) -> Event:
        saved_event = await self._memory.append_event(session=session, event=event)
        try:
            self._persist_state(session)
        except redis.RedisError:
            logger.exception("Failed to persist updated session state")

        try:
            self._history.save_adk_event(
                session_id=session.id,
                user_id=session.user_id,
                author=event.author,
                content_parts=self._event_content_parts(event),
                tool_calls=self._event_tool_calls(event),
            )
        except Exception:
            logger.exception("Failed to persist session history event")

        return saved_event


def create_session_service() -> BaseSessionService:
    """Factory used by runners to enable Redis-backed session continuity."""
    return RedisBackedSessionService()