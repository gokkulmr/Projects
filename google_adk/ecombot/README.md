# eComBot — Multi-Agent E-Commerce AI Platform

An AI-powered e-commerce customer support and sales platform built using **Google ADK (Agent Development Kit)** with multi-agent orchestration, RAG knowledge base, MCP microservices, LiteLLM gateway routing, and a rich Chainlit web UI.

---

## 🏗️ Architecture Overview

```
                    ┌─────────────────────────┐
                    │   Chainlit Web UI (v7)   │  ← Day 10
                    │   or CLI Chat Interface  │
                    └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │     Orchestrator Agent    │  ← Day 9
                    │   (Intent Classification) │
                    └─────┬──────────┬─────────┘
                          │          │
              ┌───────────▼──┐  ┌───▼───────────┐
              │ Support Agent │  │  Sales Agent   │
              │ (Orders, FAQ) │  │ (Products,     │
              │              │  │  Recommendations)│
              └──┬───┬───┬──┘  └──┬───┬─────────┘
                 │   │   │        │   │
        ┌────────┘   │   └──┐     │   └──────┐
        ▼            ▼      ▼     ▼          ▼
  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
  │PostgreSQL│ │  Redis   │ │ChromaDB │ │ FastMCP │
  │(Orders,  │ │(Sessions)│ │ (RAG)   │ │(External│
  │Products) │ │          │ │         │ │  Tools) │
  └──────────┘ └─────────┘ └─────────┘ └─────────┘
       Day 4       Day 4     Day 5-6     Day 8
```

### Technology Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | Google ADK 2.1.0 | Agent orchestration, tool calling, sessions |
| LLM Provider | OpenRouter (Gemini 2.5 Flash) | Language model via LiteLlm |
| LLM Gateway | LiteLLM Proxy | Multi-model routing & fallback (Day 7) |
| Database | PostgreSQL 16 | Orders, products, conversation history |
| Session Store | Redis 7.4 | In-memory session persistence |
| Vector DB | ChromaDB | RAG knowledge base (products + FAQ) |
| Microservices | FastMCP | External order & inventory APIs |
| Web UI | Chainlit | Rich conversational interface (Day 10) |

---

## 📋 Prerequisites

- **Python 3.11+**
- **Docker Desktop** (for Redis, PostgreSQL)
- **OpenRouter API key** ([get one here](https://openrouter.ai))

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate to the project
cd ecombot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env   # Edit with your API key

# 4. Start infrastructure
docker-compose up -d

# 5. Index the knowledge base
python -m src.rag.embed_catalog --reset

# 6. Run the agent (choose one):
python -m src.agents.support_agent      # v5 — Single agent CLI
python -m src.agents.orchestrator       # v6 — Multi-agent CLI
chainlit run src/ui/chainlit_app.py -w  # v7 — Web UI
```

---

## 📅 Day-by-Day Progression & How to Run

### Day 01 + Day 02 — Foundation & Prompt Engineering

**Goal:** Set up the ADK project, create the first LLM agent, and refine behavior through prompt engineering.

**What was built:**
- Project scaffolding with Google ADK
- Support agent with `LlmAgent` + `LiteLlm` (OpenRouter)
- Product and Sales agent variants with different instruction prompts
- Manual test cases for prompt evaluation

**How to run:**
```bash
# Run the basic support agent
python -m src.agents.support_agent

# Run the product agent variant
python -m src.agents.product_agent

# Run the sales agent variant
python -m src.agents.sales_agent
```

**Test scenarios:**
| You Type | Expected Behavior |
|----------|-------------------|
| `Hi, my name is Priya` | Agent greets Priya, remembers name |
| `What can you help me with?` | Lists e-commerce support capabilities |
| `Write me some Python code` | Politely refuses — out of scope |
| `What's the weather?` | Politely refuses — out of scope |

**Key files:** `src/agents/support_agent.py`, `src/agents/support_instructions_v1.txt`, `src/config/settings.py`

---

### Day 03 — Tool Calling & Session State

**Goal:** Add callable tools and in-memory session state for order lookups and product searches.

**What was built:**
- `get_order_status(order_id)` — queries PostgreSQL for order details
- `cancel_order(order_id)` — cancels orders with validation
- `lookup_product(product_name)` — searches products by name
- `ToolContext.state` for remembering order IDs and products across turns

**How to run:**
```bash
# Ensure Docker is running (PostgreSQL needed)
docker-compose up -d

# Run the agent
python -m src.agents.support_agent
```

**Test scenarios:**
| You Type | Expected |
|----------|----------|
| `Where is my order ORD-001?` | Calls `get_order_status`, returns shipped status |
| `What about that same order?` | Reuses ORD-001 from session state |
| `Show me Wireless Headphones` | Calls `lookup_product`, returns product details |
| `Cancel order ORD-004` | Calls `cancel_order`, confirms cancellation |
| `Track order XYZ-100` | "Invalid order ID format" |
| `Cancel ORD-001` | "Cannot cancel — already shipped" |

---

### Day 04 — Redis Sessions & PostgreSQL Backend

**Goal:** Replace in-memory data with Redis (sessions) and PostgreSQL (orders, products, history).

**What was built:**
- `docker-compose.yml` — Redis + PostgreSQL containers
- `RedisBackedSessionService` — sessions survive process restarts
- `HistoryService` — conversation history in PostgreSQL
- Repository pattern for database access

**How to run:**
```bash
# Start infrastructure
docker-compose up -d

# Verify containers are healthy
docker-compose ps

# Initialize database (auto-runs on first start via init_db.sql)
# If needed manually:
# docker exec -i adk_postgres psql -U adk_user -d adk_app < src/scripts/init_db.sql

# Run the agent
python -m src.agents.support_agent
```

**Session persistence test:**
1. Run agent, ask about `ORD-001`
2. Type `exit`
3. Run agent again
4. Ask "What was my last order?" — agent remembers from Redis

---

### Day 05 & Day 06 — RAG Knowledge Base

**Goal:** Add ChromaDB vector database for semantic search over products, FAQ, and PDF documents.

**What was built:**
- `embed_catalog.py` — indexes products.json and faq.json into ChromaDB
- `pdf_ingestor.py` — indexes PDF documents with section-aware chunking
- `retriever.py` — semantic search with distance-based relevance filtering
- `search_knowledge_base` tool with hallucination guards

**How to run:**
```bash
# Index the JSON knowledge base
python -m src.rag.embed_catalog --reset

# Index the PDF FAQ (optional)
python -m src.rag.pdf_ingestor data/ecom_faq.pdf

# Test the retriever directly
python -m src.rag.retriever "What is the return policy?"

# Run the agent with RAG
python -m src.agents.support_agent
```

**Test scenarios:**
| You Type | Expected |
|----------|----------|
| `What is your return policy?` | Searches knowledge base, returns policy details |
| `What warranty do the headphones have?` | Returns warranty info from products.json |
| `Do you offer international shipping?` | Returns FAQ answer |
| `What is the iPhone 15 warranty?` | "Not found in knowledge base" — no hallucination |

---

### Day 07 — LiteLLM Gateway Routing

**Goal:** Route LLM calls through a LiteLLM proxy with model groups and automatic fallback.

**What was built:**
- `litellm_config.yaml` — defines `fast-faq` and `deep-support` model groups
- `QueryRouter` — classifies queries by complexity
- `GatewayClient` — builds proxy-backed LiteLlm instances with fallback

**How to run:**
```bash
# Start the LiteLLM proxy (in a separate terminal)
litellm --config src/gateway/litellm_config.yaml --port 4000

# Enable gateway in .env
echo "LITELLM_PROXY_ENABLED=True" >> .env

# Run the agent
python -m src.agents.support_agent
```

You'll see routing logs like:
```
[fast-faq route selected: Simple signal (score=-0.20)]
[deep-support route selected: Complex signal (score=+0.40)]
```

**Run automated tests:**
```bash
pytest tests/test_litellm_routing.py -v
```

---

### Day 08 — FastMCP External Integrations

**Goal:** Expose order and inventory tools as external microservices via FastMCP.

**What was built:**
- `orders_server.py` — FastMCP server on port 8001 (order status, details, cancellation)
- `inventory_server.py` — FastMCP server on port 8002 (stock check, variants)
- `mcp_order_tools.py` — ADK tool wrappers that proxy to MCP servers
- Mock data with error simulation (timeout, server error)

**How to run (3 terminals):**
```bash
# Terminal 1: Start Orders MCP server
python -m src.services.mcp_servers.orders_server

# Terminal 2: Start Inventory MCP server
python -m src.services.mcp_servers.inventory_server

# Terminal 3: Enable MCP and run the agent
# Set MCP_ENABLED=True in .env first
python -m src.agents.support_agent
```

**Test scenarios:**
| You Type | Expected |
|----------|----------|
| `Check order ORD-001` | Calls MCP orders server, returns shipped status |
| `Is the Mechanical Keyboard in stock?` | Calls MCP inventory server, reports out of stock |
| `Check order ORD-999` | Timeout simulation — graceful error message |

**Run automated tests:**
```bash
pytest tests/test_mcp_integration.py -v
```

**Test MCP servers directly with curl:**
```bash
# Order status
curl -X POST http://localhost:8001/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_order_status","arguments":{"order_id":"ORD-001"}}}'

# Stock check
curl -X POST http://localhost:8002/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"check_stock","arguments":{"product_id":"PRD-101"}}}'
```

---

### Day 09 — Multi-Agent Orchestration (eComBot v6)

**Goal:** Transform the single agent into a multi-agent system with Orchestrator → Support/Sales delegation.

**What was built:**
- `orchestrator.py` — root agent with ADK `sub_agents` list
- `orchestrator_instructions.txt` — routing rules for delegation
- Refined `support_instructions_v2.txt` and `sales_instructions_v2.txt`
- `tracing.py` — delegation decision logging and trace reports
- Pattern-based intent classification (support/sales/mixed/self)

**How to run:**
```bash
# Ensure Docker is running
docker-compose up -d

# Run the multi-agent orchestrator
python -m src.agents.orchestrator
```

You'll see routing logs:
```
==================================================
 eComBot v6 — Multi-Agent Orchestrator
==================================================
 Agents: Orchestrator → Support | Sales
==================================================

You: Where is my order ORD-001?
  [SUPPORT → support_agent] 2 support signal(s) detected

You: Recommend headphones under ₹3000
  [SALES → sales_agent] 2 sales signal(s) detected

You: trace
  ============================================================
   ORCHESTRATION TRACE REPORT
  ============================================================
```

**Test scenarios:**
| You Type | Routing | Agent |
|----------|---------|-------|
| `Where is my order ORD-001?` | SUPPORT | support_agent |
| `Recommend a good keyboard` | SALES | sales_agent |
| `Check ORD-004 and suggest alternatives` | MIXED | support → sales |
| `Hello! What can you do?` | SELF | orchestrator |
| `What's your return policy?` | SUPPORT | support_agent |

Type `trace` at any time to see the full delegation trace report.

---

### Day 10 — Generative UI with Chainlit (eComBot v7)

**Goal:** Rich web UI with structured cards, tool-call steps, action buttons, and session state.

**What was built:**
- `chainlit_app.py` — Chainlit web application wired to the Orchestrator
- `card_renderers.py` — markdown card renderers for orders, products, stock
- `.chainlit/config.toml` — UI theme and configuration
- Action buttons for quick actions and follow-ups
- Session state for multi-turn context

**How to run:**

```bash
# Step 1: Ensure infrastructure is running
docker-compose up -d

# Step 2: Index knowledge base (first time only)
python -m src.rag.embed_catalog --reset

# Step 3: (Optional) Start MCP servers if using external tools
python -m src.services.mcp_servers.orders_server   # Terminal 2
python -m src.services.mcp_servers.inventory_server  # Terminal 3

# Step 4: Start the Chainlit web UI
chainlit run src/ui/chainlit_app.py -w
```

**Open browser:** http://localhost:8000

**UI Features:**
- 🏠 **Welcome screen** with quick-action buttons (Check Order, Browse Products, FAQ)
- 📦 **Structured cards** for order status and product details
- 🔧 **Tool call steps** visible as expandable sections
- 🔘 **Action buttons** for follow-ups (cancel order, return policy, budget filters)
- 💾 **Session memory** — remembers order IDs and products across turns

**Test flows:**
1. Click "📦 Check Order Status" → Type `ORD-001` → See order card + follow-up buttons
2. Type "Recommend headphones" → See product results + budget filter buttons
3. Click "❓ FAQ & Policies" → Click "🚚 Shipping" → See shipping info
4. Type "Check ORD-004" then "Can I cancel it?" → Session remembers the order

See `docs/Day10_Documentation.md` for the complete step-by-step guide.

---

## 📁 Project Structure

```
ecombot/
├── .chainlit/
│   └── config.toml                    # Chainlit UI configuration (Day 10)
├── .chromadb/                         # ChromaDB vector database (Day 5-6)
├── data/
│   ├── products.json                  # Product catalog (5 products)
│   ├── faq.json                       # FAQ entries (18 questions)
│   └── ecom_faq.pdf                   # PDF version of FAQ
├── docs/
│   ├── README.md                      # Docs index
│   ├── Day01_Day02_Documentation.md   # Foundation & prompts
│   ├── Day03_Documentation.md         # Tool calling & sessions
│   ├── Day04_Documentation.md         # Redis + PostgreSQL
│   ├── Day05_Documentation.md         # RAG with ChromaDB
│   ├── Day06_Documentation.md         # PDF ingestion
│   ├── Day07_Documentation.md         # LiteLLM Gateway
│   ├── Day08_Documentation.md         # FastMCP integration
│   ├── Day09_Documentation.md         # Multi-agent orchestration
│   └── Day10_Documentation.md         # Chainlit generative UI
├── src/
│   ├── agents/
│   │   ├── orchestrator.py            # Root orchestrator agent (Day 9)
│   │   ├── orchestrator_instructions.txt
│   │   ├── support_agent.py           # Support specialist (Day 1-8)
│   │   ├── support_instructions_v1.txt # Original support prompt
│   │   ├── support_instructions_v2.txt # Orchestrated support prompt (Day 9)
│   │   ├── product_agent.py           # Product agent variant (Day 2)
│   │   ├── product_instructions_v1.txt
│   │   ├── sales_agent.py            # Sales agent variant (Day 2)
│   │   ├── sales_instructions_v1.txt
│   │   ├── sales_instructions_v2.txt  # Orchestrated sales prompt (Day 9)
│   │   ├── tracing.py                # Delegation tracing (Day 9)
│   │   └── sessions.py               # Session factory helper
│   ├── config/
│   │   └── settings.py               # Centralized environment config
│   ├── gateway/
│   │   ├── proxy_client.py           # LiteLLM proxy client (Day 7)
│   │   ├── router.py                 # Query complexity classifier (Day 7)
│   │   └── litellm_config.yaml       # LiteLLM model groups config
│   ├── rag/
│   │   ├── embed_catalog.py          # JSON → ChromaDB indexer (Day 5)
│   │   ├── pdf_ingestor.py           # PDF → ChromaDB indexer (Day 6)
│   │   └── retriever.py             # Semantic search retriever (Day 5)
│   ├── services/
│   │   ├── db.py                     # PostgreSQL connection pool (Day 4)
│   │   ├── repositories.py          # SQL repository helpers (Day 4)
│   │   ├── session_service.py       # Redis-backed sessions (Day 4)
│   │   ├── history_service.py       # PostgreSQL history (Day 4)
│   │   ├── mcp_client.py            # MCP HTTP wrapper (Day 8)
│   │   └── mcp_servers/
│   │       ├── orders_server.py     # FastMCP orders API (Day 8)
│   │       ├── inventory_server.py  # FastMCP inventory API (Day 8)
│   │       └── mock_data.py         # In-memory mock data (Day 8)
│   ├── tools/
│   │   ├── order_tools.py           # PostgreSQL order tools (Day 3-4)
│   │   ├── product_tools.py         # PostgreSQL product tools (Day 3-4)
│   │   ├── knowledge_tools.py       # RAG knowledge search (Day 5)
│   │   └── mcp_order_tools.py       # MCP proxy tools (Day 8)
│   ├── ui/
│   │   ├── chainlit_app.py          # Chainlit web UI (Day 10)
│   │   └── card_renderers.py        # Structured card helpers (Day 10)
│   └── scripts/
│       ├── init_db.sql              # Database schema + seed data
│       └── create_pdf.py            # FAQ PDF generator
├── tests/
│   ├── test_litellm_routing.py      # Automated gateway tests
│   ├── test_mcp_integration.py      # Automated MCP tests
│   ├── test_litellm_manual.md       # Manual LiteLLM test guide
│   ├── test_mcp_manual.md           # Manual MCP test guide
│   ├── test_rag_manual.md           # Manual RAG test guide
│   ├── test_support_agent_manual.md # Manual agent test guide
│   └── test_prompt_variants.md      # Prompt variant test guide
├── .env                             # Environment variables (not in git)
├── docker-compose.yml               # Redis + PostgreSQL containers
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🗄️ Database Schema

### `orders` table
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | TEXT (PK) | e.g., `ORD-001` |
| `customer_name` | TEXT | Customer name |
| `status` | TEXT | `processing`, `shipped`, `delivered`, `cancelled` |
| `product_id` | TEXT | FK reference to products |
| `quantity` | INT | Number of items |
| `created_at` | TIMESTAMPTZ | Order creation time |

### `products` table
| Column | Type | Description |
|--------|------|-------------|
| `product_id` | TEXT (PK) | e.g., `PRD-101` |
| `name` | TEXT | Product name |
| `description` | TEXT | Description |
| `price` | NUMERIC(10,2) | Price in INR |
| `stock` | INT | Items in stock |
| `active` | BOOLEAN | Currently sold |

### Seed Data
| Order ID | Customer | Status | Product |
|----------|----------|--------|---------|
| ORD-001 | Priya Sharma | shipped | PRD-101 (Wireless Headphones) |
| ORD-002 | Rahul Menon | delivered | PRD-102 (Mechanical Keyboard) |
| ORD-003 | Anika Bose | cancelled | PRD-103 (USB-C Hub) |
| ORD-004 | Dev Nair | processing | PRD-101 (Wireless Headphones) |
| ORD-005 | Sara Pillai | shipped | PRD-102 (Mechanical Keyboard) |

---

## 🔧 Environment Variables

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Redis (default values work with docker-compose)
REDIS_HOST=127.0.0.1
REDIS_PORT=6380
REDIS_PASSWORD=change_me_redis_password

# PostgreSQL (default values work with docker-compose)
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_DB=adk_app
POSTGRES_USER=adk_user
POSTGRES_PASSWORD=change_me_postgres_password

# Optional toggles
LITELLM_PROXY_ENABLED=False    # Enable LiteLLM gateway routing (Day 7)
MCP_ENABLED=False              # Use FastMCP external tools (Day 8)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'google'` | `pip install -r requirements.txt` |
| `redis.exceptions.ConnectionError` | Start Docker: `docker-compose up -d` |
| `psycopg.errors.UndefinedTable` | Recreate DB: `docker-compose down -v && docker-compose up -d` |
| `ModuleNotFoundError: chainlit` | `pip install chainlit>=2.0.0` |
| Port 8000 in use (Chainlit) | `chainlit run src/ui/chainlit_app.py -w --port 8080` |
| Knowledge base empty | `python -m src.rag.embed_catalog --reset` |
| MCP tools timing out | Start MCP servers first, ensure `MCP_ENABLED=True` |
| `Provider List: ...litellm.ai/docs/providers` | LiteLLM info log — safe to ignore |
| `LiteLLM:ERROR: logging_worker.py` | Non-critical logging timeout — ignore |

---

## 📚 Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Chainlit Documentation](https://docs.chainlit.io/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
