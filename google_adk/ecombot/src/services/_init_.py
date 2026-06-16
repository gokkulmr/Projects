"""Service layer for storage, sessions, and history."""

try:
    from .db import DatabaseServiceError
    from .db import close_postgres_pool
    from .db import get_postgres_pool
except ImportError:
    # PostgreSQL dependencies not available
    DatabaseServiceError = Exception
    close_postgres_pool = None
    get_postgres_pool = None

try:
    from .history_service import HistoryService
except ImportError:
    HistoryService = None

try:
    from .session_service import RedisBackedSessionService
    from .session_service import create_session_service
except ImportError:
    RedisBackedSessionService = None
    create_session_service = None

__all__ = [
    "DatabaseServiceError",
    "get_postgres_pool",
    "close_postgres_pool",
    "HistoryService",
    "RedisBackedSessionService",
    "create_session_service",
]