# eComBot — E-commerce Customer Support Agent

An AI-powered e-commerce customer support chatbot built using **Google ADK (Agent Development Kit)** with **OpenRouter LLM**, **Redis** for session persistence, and **PostgreSQL** for durable data storage.

---

## Project Overview

This project is part of a multi-day capstone that incrementally builds a production-ready AI support agent. Each day adds a new capability layer.

---

## Day-by-Day Progression

### Day 01 + Day 02 — Foundation & Prompt Engineering

**Goal:** Set up the ADK project, create the first LLM agent, and refine its behavior through prompt engineering.

| File | Purpose |
|------|---------|
| `src/agents/support_agent.py` | Main support agent — creates an `LlmAgent` with `LiteLlm` (OpenRouter), wires tools, and runs a CLI chat loop. |
| `src/agents/product_agent.py` | Standalone product-focused agent variant (Day 02 experiment). |
| `src/agents/sales_agent.py` | Standalone sales-focused agent variant (Day 02 experiment). |
| `src/agents/support_instructions_v1.txt` | System prompt for the support agent — defines scope, tool usage rules, and behavior. |
| `src/agents/product_instructions_v1.txt` | System prompt variant for the product agent. |
| `src/agents/sales_instructions_v1.txt` | System prompt variant for the sales agent. |
| `src/agents/sessions.py` | Session factory helper (Day 01/02 — uses `InMemorySessionService`). |
| `src/config/settings.py` | Centralized configuration — reads all secrets and endpoints from `.env`. |
| `.env` | Environment variables (API keys, DB credentials). **Not committed to git.** |
| `requirements.txt` | Python dependencies. |

**Key concepts introduced:**
- Google ADK `LlmAgent` + `LiteLlm` for OpenRouter integration
- Prompt engineering with multiple instruction variants
- In-scope vs out-of-scope behavior control

---

### Day 03 — Tool Calling & In-Memory Session State

**Goal:** Add the first callable tool (`get_order_status`) and in-memory session state so the agent can look up real data and remember context across turns.

| File | Purpose |
|------|---------|
| `src/tools/order_tools.py` | `get_order_status(order_id)` — validates format, queries PostgreSQL, returns structured result. `cancel_order(order_id)` — cancels an order if not already shipped/delivered. |
| `src/tools/product_tools.py` | `lookup_product(product_name)` — searches products by name via PostgreSQL. |
| `tests/test_support_agent_manual.md` | Manual test cases for validating agent behavior (core flow + failure scenarios). |

**Key concepts introduced:**
- `@tool` decorator for ADK tool registration
- Input validation (regex for order ID format)
- Structured tool responses (`{"ok": true/false, ...}`)
- `ToolContext.state` for storing `last_order_id`, `current_product_id`, `last_intent`

---

### Day 04 — Redis Session Persistence & PostgreSQL Tools

**Goal:** Replace in-memory data with real infrastructure. Redis provides session continuity across restarts. PostgreSQL provides durable storage for orders, products, and conversation history.

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines Redis and PostgreSQL containers with health checks, passwords, and volumes. |
| `src/scripts/init_db.sql` | Creates `orders`, `products`, and `session_history` tables. Seeds demo data (5 orders, 5 products). |
| `src/config/settings.py` | Updated with Redis and PostgreSQL connection settings. Builds `redis_url()` and `postgres_dsn()`. |
| `src/services/db.py` | Reusable PostgreSQL connection pool (`psycopg_pool`). Provides `fetch_one()`, `fetch_all()`, `execute()` helpers. |
| `src/services/repositories.py` | Repository pattern — `OrdersRepository` and `ProductsRepository` keep SQL queries out of tool code. |
| `src/services/session_service.py` | `RedisBackedSessionService` — wraps ADK's `InMemorySessionService` with Redis persistence. Restores session state after app restart. Also persists conversation turns to PostgreSQL via `HistoryService`. |
| `src/services/history_service.py` | Saves each conversation turn (user/assistant/tool) to the `session_history` table in PostgreSQL. |
| `src/services/_init_.py` | Service layer package init — exports DB, session, and history services. |

**Key concepts introduced:**
- Redis for short-lived session memory (survives process restarts)
- PostgreSQL for durable business data and conversation history
- Connection pooling with `psycopg_pool`
- `docker-compose` infrastructure with health checks
- Separation: Redis = working memory, PostgreSQL = durable storage

### Day 05 & Day 06 — RAG Knowledge Base & Hallucination Guards

**Goal:** Add a local vector database (ChromaDB) and grounding layer so the agent can accurately answer factual product questions, warranty policies, and general FAQs without inventing facts.

| File | Purpose |
|------|---------|
| `data/products.json` & `faq.json` | The raw knowledge base containing technical specifications, return policies, and FAQs. |
| `data/ecom_faq.pdf` | An auto-generated PDF version of the FAQ to validate PDF ingestion. |
| `src/rag/embed_catalog.py` | Parses and chunks the JSON catalogs, then upserts embeddings and metadata into ChromaDB. |
| `src/rag/pdf_ingestor.py` | Extracts text from PDFs (`pypdf`), chunks using overlapping sections, and embeds into ChromaDB. |
| `src/rag/retriever.py` | Connects to ChromaDB and retrieves the top-K relevant text chunks with metadata for a query. |
| `src/tools/knowledge_tools.py` | Exposes the `search_knowledge_base` tool to the agent. Implements relevance filters (distance thresholds) to prevent bad answers. |
| `tests/test_rag_manual.md` | Manual test cases for RAG (Clean match, Partial match, Hallucination traps, Fallbacks). |

**Key concepts introduced:**
- Local ChromaDB vector database (`ecombot_kb` collection)
- Open-source, local embedding model (`all-MiniLM-L6-v2`) via `sentence-transformers`
- Retrieval-Augmented Generation (RAG)
- Section-aware PDF chunking with overlap and rich metadata extraction
- Hallucination guards via strict LLM instructions and graceful failover/fallback logic

---

## Database Schema

### `orders` table
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | TEXT (PK) | e.g., `ORD-001` |
| `customer_name` | TEXT | Customer who placed the order |
| `status` | TEXT | `processing`, `shipped`, `delivered`, `cancelled` |
| `product_id` | TEXT | FK reference to products |
| `quantity` | INT | Number of items |
| `created_at` | TIMESTAMPTZ | Order creation time |

### `products` table
| Column | Type | Description |
|--------|------|-------------|
| `product_id` | TEXT (PK) | e.g., `PRD-101` |
| `name` | TEXT | Product name |
| `description` | TEXT | Product description |
| `price` | NUMERIC(10,2) | Price in INR |
| `stock` | INT | Items in stock |
| `active` | BOOLEAN | Whether product is currently sold |

### `session_history` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-increment ID |
| `session_id` | TEXT | ADK session identifier |
| `user_id` | TEXT | User identifier |
| `role` | TEXT | `user`, `assistant`, or `tool` |
| `content` | TEXT | Message content |
| `tool_calls` | JSONB | Tool call details (if any) |
| `created_at` | TIMESTAMPTZ | Timestamp |

### Seed Data

**Orders:**
| Order ID | Customer | Status | Product |
|----------|----------|--------|---------|
| ORD-001 | Priya Sharma | shipped | PRD-101 |
| ORD-002 | Rahul Menon | delivered | PRD-102 |
| ORD-003 | Anika Bose | cancelled | PRD-103 |
| ORD-004 | Dev Nair | processing | PRD-101 |
| ORD-005 | Sara Pillai | shipped | PRD-102 |

**Products:**
| Product ID | Name | Price | Stock | Active |
|------------|------|-------|-------|--------|
| PRD-101 | Wireless Headphones | ₹2,499 | 50 | ✅ |
| PRD-102 | Mechanical Keyboard | ₹3,999 | 0 | ✅ |
| PRD-103 | USB-C Hub | ₹1,299 | 20 | ✅ |
| PRD-104 | Webcam 4K | ₹5,499 | 15 | ✅ |
| PRD-105 | Old Mouse | — | 0 | ❌ |

---

## Project Structure

```
ecombot/
├── src/
│   ├── .adk/                          # ADK internal session DB
│   ├── _init_.py                      # Package init
│   ├── agents/
│   │   ├── support_agent.py           # Main agent (Day 01-04)
│   │   ├── support_instructions_v1.txt # Agent system prompt
│   │   ├── product_agent.py           # Product agent variant (Day 02)
│   │   ├── product_instructions_v1.txt # Product agent prompt
│   │   ├── sales_agent.py             # Sales agent variant (Day 02)
│   │   ├── sales_instructions_v1.txt  # Sales agent prompt
│   │   └── sessions.py               # Session factory helper
│   ├── tools/
│   │   ├── order_tools.py             # get_order_status, cancel_order (Day 03-04)
│   │   └── product_tools.py           # lookup_product (Day 03-04)
│   ├── services/
│   │   ├── _init_.py                  # Service exports
│   │   ├── db.py                      # PostgreSQL connection pool (Day 04)
│   │   ├── repositories.py            # SQL repository helpers (Day 04)
│   │   ├── session_service.py         # Redis-backed sessions (Day 04)
│   │   └── history_service.py         # PostgreSQL history (Day 04)
│   ├── config/
│   │   └── settings.py               # Centralized config from .env
│   └── scripts/
│       └── init_db.sql               # DB schema + seed data
├── tests/
│   └── test_support_agent_manual.md   # Manual test cases
├── .env                               # Environment variables (not in git)
├── docker-compose.yml                 # Redis + PostgreSQL containers
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

---

## Setup & Running

### Prerequisites

- Python 3.11+
- Docker Desktop (for Redis & PostgreSQL)
- OpenRouter API key

### 1. Install Python dependencies

```bash
cd ecombot
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the `ecombot/` directory:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here

REDIS_HOST=127.0.0.1
REDIS_PORT=6380
REDIS_PASSWORD=change_me_redis_password

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_DB=adk_app
POSTGRES_USER=adk_user
POSTGRES_PASSWORD=change_me_postgres_password
```

### 3. Start infrastructure (Redis + PostgreSQL)

```bash
docker-compose up -d
```

This will:
- Start Redis on port `6380` with password protection
- Start PostgreSQL on port `5433` with the `adk_app` database
- Automatically run `init_db.sql` to create tables and seed data

Verify containers are healthy:
```bash
docker-compose ps
```

### 4. Run the agent

```bash
python -m src.agents.support_agent
```

You will see the interactive chat prompt:
```
====================================
 E-commerce Support Agent
====================================
Type 'exit' to quit

You:
```

---

## Testing

### Core Flow Test

| Turn | You Type | What Should Happen |
|------|----------|-------------------|
| 1 | `Hi, my name is Priya.` | Agent greets Priya, stores name in session |
| 2 | `Where is my order ORD-001?` | Agent calls `get_order_status`, returns order details from PostgreSQL |
| 3 | `What about that same order?` | Agent reuses `ORD-001` from session state |
| 4 | `Show me Wireless Headphones` | Agent calls `lookup_product`, returns product details |
| 5 | `What is the price again?` | Agent reuses product info from session |
| 6 | `Cancel order ORD-004` | Agent calls `cancel_order`, confirms cancellation |

### Failure Handling Test

| You Type | Expected |
|----------|----------|
| `Check order ORD-999` | "Order ORD-999 not found." |
| `Cancel my order` | Agent asks for order ID |
| `Track order XYZ-100` | "Invalid order ID format." |
| `Cancel ORD-001` | "Cannot cancel — already shipped." |
| `Cancel ORD-003` | "Already cancelled." |

### Session Persistence Test

1. Run the agent, ask about `ORD-001`
2. Type `exit`
3. Run the agent again
4. Ask "Is my order still delayed?" — the agent should remember `ORD-001` from Redis

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'google'` | Run `pip install -r requirements.txt` |
| `redis.exceptions.ConnectionError` | Make sure Docker containers are running: `docker-compose up -d` |
| `psycopg.errors.UndefinedTable` | PostgreSQL init script didn't run. Recreate: `docker-compose down -v && docker-compose up -d` |
| `Provider List: https://docs.litellm.ai/docs/providers` | This is a LiteLLM info log, not an error. Can be ignored. |
| `LiteLLM:ERROR: logging_worker.py` | Non-critical logging timeout. Can be ignored. |
