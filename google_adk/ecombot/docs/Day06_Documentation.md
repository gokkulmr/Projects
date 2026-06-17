# Day 6: Database Integration

## Overview
We transition from mock JSON and in-memory lists to a robust PostgreSQL and Redis stack via Docker Compose. Tools and sessions now persist permanently across restarts.

## Learning Objectives
- Using `docker-compose` to run local databases.
- Integrating `psycopg_pool` into ADK tool functions.
- Extending ADK's `BaseSessionService` to use Redis hash storage.
- Building a PostgreSQL conversation history logger.

## Architecture
- **PostgreSQL**: Stores the `orders` table, the `products` table, and `session_history`.
- **Redis**: Stores the `InMemorySessionService` equivalents using TTL hashes.

## Files Created/Modified

### `docker-compose.yml`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/docker-compose.yml`
- **Purpose**: Instantiates postgres:16-alpine and redis:7.4-alpine.
- **Key Components**: Volumes, healthchecks, entrypoint script execution.

### `init_db.sql`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/scripts/init_db.sql`
- **Purpose**: Seeds the DB on first startup.

### `db.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/services/db.py`
- **Purpose**: Manages the PostgreSQL connection pool.
- **Key Components**: `get_connection()`, `fetch_one()`, `execute()`.

### `session_service.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/services/session_service.py`
- **Purpose**: Redis-backed ADK session implementation.
- **Key Components**: Subclasses `BaseSessionService`, uses `redis.hset`.

## How to Run / Test

### Starting the Infrastructure
1. Start the Redis and PostgreSQL containers in the background:
   ```bash
   docker-compose up -d
   ```
2. Start the support agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Session Continuity Across Restarts**
- **Turn 1 (User Input)**: "Hi, my name is John."
- **Action**: Stop the `support_agent.py` process (Ctrl+C).
- **Turn 2 (Action)**: Restart `python src/agents/support_agent.py`.
- **Turn 3 (User Input)**: "What is my name?"
- **Expected Outcome**: The agent replies "John". The in-memory session was lost during the restart, but ADK seamlessly reconstructed it from the Redis hash store.

**Test Case 2: Database Tool Persistence**
- **User Input**: "Cancel my order ORD-004."
- **Expected Outcome**: The agent uses PostgreSQL to cancel the order. If you connect to the `adk_app` database directly via psql/pgAdmin, you will see the status row updated permanently.

## Key Concepts Covered
- Connection pooling in Python async environments.
- Redis caching for ADK sessions.
- SQL Table initialization via Docker volumes.
