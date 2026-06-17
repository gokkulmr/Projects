"""Runtime configuration for eComBot."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env", override=False)


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# -----------------------
# LLM & OpenRouter Config
# -----------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = _env("OPENROUTER_MODEL", "openrouter/google/gemini-2.5-flash")
OPENROUTER_BASE_URL = _env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

LLM_MODEL = _env("LLM_MODEL", OPENROUTER_MODEL)
LLM_BASE_URL = _env("LLM_BASE_URL", OPENROUTER_BASE_URL)
LLM_API_KEY = _env("LLM_API_KEY", OPENROUTER_API_KEY)
LLM_CUSTOM_PROVIDER = os.getenv("LLM_CUSTOM_PROVIDER", "").strip() or None
LLM_REQUEST_TIMEOUT_SECONDS = float(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "20"))


# -----------------------
# Redis Config (Session)
# -----------------------
REDIS_HOST = _env("REDIS_HOST", "127.0.0.1")
REDIS_PORT = _env_int("REDIS_PORT", 6379)
REDIS_PASSWORD = _env("REDIS_PASSWORD", "")
REDIS_DB = _env_int("REDIS_DB", 0)
REDIS_SESSION_TTL_SECONDS = _env_int("REDIS_SESSION_TTL_SECONDS", 86400)


# -----------------------
# PostgreSQL Config (Tools & History)
# -----------------------
POSTGRES_HOST = _env("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = _env_int("POSTGRES_PORT", 5433)
POSTGRES_DB = _env("POSTGRES_DB", "adk_app")
POSTGRES_USER = _env("POSTGRES_USER", "adk_user")
POSTGRES_PASSWORD = _env("POSTGRES_PASSWORD", "")
POSTGRES_MIN_CONNECTIONS = _env_int("POSTGRES_MIN_CONNECTIONS", 1)
POSTGRES_MAX_CONNECTIONS = _env_int("POSTGRES_MAX_CONNECTIONS", 10)


def redis_url() -> str:
    """Build Redis URL from env configuration."""
    auth = f":{quote_plus(REDIS_PASSWORD)}@" if REDIS_PASSWORD else ""
    return f"redis://{auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


def postgres_dsn() -> str:
    """Build PostgreSQL DSN from env configuration."""
    return (
        "postgresql://"
        f"{quote_plus(POSTGRES_USER)}:{quote_plus(POSTGRES_PASSWORD)}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


REDIS_URL = redis_url()
POSTGRES_DSN = postgres_dsn()


# -----------------------
# ChromaDB Config (RAG)
# -----------------------
CHROMA_PERSIST_DIR = Path(
    _env("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / ".chromadb"))
)
CHROMA_COLLECTION_NAME = _env("CHROMA_COLLECTION_NAME", "ecombot_kb")


# -----------------------
# LiteLLM Gateway Config
# -----------------------
LITELLM_PROXY_ENABLED = _env_bool("LITELLM_PROXY_ENABLED", False)
LITELLM_PROXY_URL = _env("LITELLM_PROXY_URL", "http://localhost:4000")
LITELLM_PROXY_API_KEY = _env("LITELLM_PROXY_API_KEY", "")
LITELLM_FAST_MODEL = _env("LITELLM_FAST_MODEL", "fast-faq")
LITELLM_DEEP_MODEL = _env("LITELLM_DEEP_MODEL", "deep-support")
LITELLM_FALLBACK_ENABLED = _env_bool("LITELLM_FALLBACK_ENABLED", True)
LITELLM_MAX_RETRIES = _env_int("LITELLM_MAX_RETRIES", 2)
LITELLM_TIMEOUT_SECONDS = float(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))


# -----------------------
# FastMCP Config
# -----------------------
MCP_ORDERS_HOST = _env("MCP_ORDERS_HOST", "127.0.0.1")
MCP_ORDERS_PORT = _env_int("MCP_ORDERS_PORT", 8001)
MCP_INVENTORY_HOST = _env("MCP_INVENTORY_HOST", "127.0.0.1")
MCP_INVENTORY_PORT = _env_int("MCP_INVENTORY_PORT", 8002)
MCP_TIMEOUT_SECONDS = float(os.getenv("MCP_TIMEOUT_SECONDS", "10"))
MCP_ENABLED = _env_bool("MCP_ENABLED", False)



# -----------------------
# LiteLLM Gateway Config
# -----------------------
LITELLM_PROXY_ENABLED = _env_bool("LITELLM_PROXY_ENABLED", False)
LITELLM_PROXY_URL = _env("LITELLM_PROXY_URL", "http://localhost:4000")
LITELLM_PROXY_API_KEY = _env("LITELLM_PROXY_API_KEY", "")
LITELLM_FAST_MODEL = _env("LITELLM_FAST_MODEL", "fast-faq")
LITELLM_DEEP_MODEL = _env("LITELLM_DEEP_MODEL", "deep-support")
LITELLM_FALLBACK_ENABLED = _env_bool("LITELLM_FALLBACK_ENABLED", True)
LITELLM_MAX_RETRIES = _env_int("LITELLM_MAX_RETRIES", 2)
LITELLM_TIMEOUT_SECONDS = float(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))