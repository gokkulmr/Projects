"""Reusable PostgreSQL connection layer."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any
from typing import Iterator
from typing import Sequence

from psycopg import Error as PsycopgError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from config.settings import POSTGRES_DSN
from config.settings import POSTGRES_MAX_CONNECTIONS
from config.settings import POSTGRES_MIN_CONNECTIONS

logger = logging.getLogger(__name__)


class DatabaseServiceError(RuntimeError):
    """Raised when the application cannot read/write PostgreSQL safely."""


_pool: ConnectionPool | None = None


def get_postgres_pool() -> ConnectionPool:
    """Return a singleton PostgreSQL connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=POSTGRES_DSN,
            min_size=POSTGRES_MIN_CONNECTIONS,
            max_size=POSTGRES_MAX_CONNECTIONS,
            kwargs={"autocommit": True, "row_factory": dict_row},
            open=True,
        )
    return _pool


def close_postgres_pool() -> None:
    """Close the shared PostgreSQL connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection() -> Iterator[Any]:
    """Yield a live database connection from the pool."""
    pool = get_postgres_pool()
    try:
        with pool.connection() as conn:
            yield conn
    except PsycopgError as exc:
        logger.exception("PostgreSQL connection failure")
        raise DatabaseServiceError("Database is unavailable right now.") from exc


def fetch_one(query: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
    """Run a SELECT query and return a single row as dict."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchone()
        except PsycopgError as exc:
            logger.exception("PostgreSQL fetch_one failed")
            raise DatabaseServiceError("Unable to read from database.") from exc


def fetch_all(query: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    """Run a SELECT query and return all rows as dict list."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return list(cur.fetchall())
        except PsycopgError as exc:
            logger.exception("PostgreSQL fetch_all failed")
            raise DatabaseServiceError("Unable to read from database.") from exc


def execute(query: str, params: Sequence[Any] | None = None) -> int:
    """Run INSERT/UPDATE/DELETE and return affected row count."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.rowcount
        except PsycopgError as exc:
            logger.exception("PostgreSQL execute failed")
            raise DatabaseServiceError("Unable to update database.") from exc