# Day 10: Generative UI with Chainlit (eComBot v7)

## Overview
We give eComBot a rich web-based UI using Chainlit, replacing the CLI chat interface. The UI exposes structured cards, visible tool-call steps, action buttons, and session state for a production-like experience.

## Learning Objectives
- Building conversational UIs with Chainlit
- Structured data rendering (cards, tables)
- Tool-call visualization with `@cl.step`
- Interactive action buttons with `@cl.action_callback`
- Multi-turn session state with `cl.user_session`

## Architecture

```
Browser (Chainlit UI)
    │
    ▼
┌──────────────────┐
│ chainlit_app.py  │
│ ┌──────────────┐ │
│ │ @cl.on_message│ │  ← User message
│ │ process_msg() │ │  ← Calls orchestrator
│ │ @cl.Step      │ │  ← Shows tool calls
│ │ cl.Action     │ │  ← Follow-up buttons
│ │ cl.user_session│ │  ← Remembers context
│ └──────────────┘ │
└────────┬─────────┘
         │
         ▼
   Orchestrator
   ├── Support Agent
   └── Sales Agent
```

## Prerequisites

### Install Chainlit
```bash
pip install chainlit>=2.0.0
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Ensure Infrastructure is Running
```bash
# Start Redis + PostgreSQL
docker-compose up -d

# Verify containers are healthy
docker-compose ps
```

### Ensure Knowledge Base is Indexed
```bash
# Index product catalog and FAQ into ChromaDB
python -m src.rag.embed_catalog --reset

# Optionally index the PDF FAQ
python -m src.rag.pdf_ingestor data/ecom_faq.pdf
```

## Files Created

### `chainlit_app.py`
- **Path**: `src/ui/chainlit_app.py`
- **Purpose**: Main Chainlit application — the web UI entry point
- **Key Components**:
  - `@cl.on_chat_start` — Initializes session, creates runner, shows welcome message with quick-action buttons
  - `@cl.on_message` — Receives user messages and delegates to `process_message()`
  - `process_message()` — Core handler: calls orchestrator, tracks tool calls as `@cl.Step`, renders responses with follow-up actions
  - `@cl.action_callback` handlers — Handle button clicks (order check, browse products, FAQ topics, budget selection, follow-ups)

### `card_renderers.py`
- **Path**: `src/ui/card_renderers.py`
- **Purpose**: Helper functions to render structured markdown cards
- **Functions**: `render_order_card()`, `render_product_card()`, `render_stock_card()`

### `.chainlit/config.toml`
- **Path**: `.chainlit/config.toml`
- **Purpose**: Chainlit configuration (project name, theme, telemetry)

## Step-by-Step: Running the Chainlit UI

### Step 1: Navigate to the project directory
```bash
cd ecombot
```

### Step 2: Ensure your `.env` file is configured
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

### Step 3: Start the infrastructure
```bash
docker-compose up -d
```

### Step 4: Index the knowledge base (first time only)
```bash
python -m src.rag.embed_catalog --reset
```

### Step 5: Start the Chainlit app
```bash
chainlit run src/ui/chainlit_app.py -w
```

The `-w` flag enables hot-reload for development.

### Step 6: Open the UI
Open your browser to: **http://localhost:8000**

You should see the eComBot welcome message with three quick-action buttons:
- 📦 Check Order Status
- 🛍️ Browse Products
- ❓ FAQ & Policies

### Step 7: (Optional) If using MCP tools
Start the FastMCP servers in separate terminals first:
```bash
# Terminal 1
python src/services/mcp_servers/orders_server.py

# Terminal 2
python src/services/mcp_servers/inventory_server.py
```

Set `MCP_ENABLED=True` in `.env`, then restart Chainlit.

## UI Features Walkthrough

### Feature 1: Welcome Screen with Action Buttons
On first load, the user sees a welcome message and three buttons:
- **Check Order Status** — prompts for order ID
- **Browse Products** — auto-sends a product query
- **FAQ & Policies** — shows sub-topic buttons (Return Policy, Shipping, Warranty, Payment)

### Feature 2: Structured Cards
When the agent retrieves order or product data, results are displayed as formatted markdown tables:

**Order Card Example:**
```
### 📦 Order ORD-001
| Field | Value |
|-------|-------|
| Customer | Priya Sharma |
| Status | Shipped |
| Product | Wireless Headphones |
| Carrier | BlueDart |
| Tracking | BD1234567890 |
| ETA | 2026-06-20 |
```

### Feature 3: Tool Call Steps
When a tool is called (e.g., `get_order_status`), a named step appears in the UI:
- 📦 Checking Order Status
- 🔍 Searching Products
- 📚 Searching Knowledge Base
- ❌ Cancelling Order

Steps are expandable to show input parameters and results.

### Feature 4: Follow-up Action Buttons
After an order lookup, follow-up buttons appear:
- ❌ Cancel ORD-XXX
- 📋 Return Policy

After product queries, budget filter buttons appear:
- 💰 Under ₹3,000
- 💰 Under ₹5,000
- 💰 Under ₹10,000

### Feature 5: Session State
The UI remembers:
- **Last order ID** — no need to repeat the order number
- **Last product** — follow-up questions reference the same product
- Context is stored via `cl.user_session`

## Verification Test Flows

### Support Journey: Order Lookup → Return
1. Click "📦 Check Order Status" button
2. Type: `ORD-001`
3. **Expected**: Order card appears showing shipped status + tool call step visible
4. Click "📋 Return Policy" follow-up button
5. **Expected**: Knowledge base is searched, return policy information displayed

### Sales Journey: Product Discovery → Budget Filter
1. Type: "Recommend me some headphones"
2. **Expected**: Product info displayed, budget buttons appear
3. Click "💰 Under ₹3,000"
4. **Expected**: Filtered recommendations based on budget

### Mixed Journey: Order + Alternatives
1. Type: "Check order ORD-004 and suggest similar products"
2. **Expected**: Order status shown (processing), then product recommendations
3. Tool call steps visible for both operations

### FAQ Journey: Policy Questions
1. Click "❓ FAQ & Policies"
2. Click "🚚 Shipping"
3. **Expected**: Shipping information from knowledge base displayed

### Multi-turn Context Test
1. Type: "Check order ORD-001"
2. **Expected**: Order details shown
3. Type: "Can I cancel it?"
4. **Expected**: Agent uses remembered ORD-001 (from session state) — responds that it can't be cancelled because it's shipped

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: chainlit` | Run `pip install chainlit>=2.0.0` |
| Port 8000 already in use | Use `chainlit run src/ui/chainlit_app.py -w --port 8080` |
| Chainlit can't find modules | Ensure you run from the `ecombot/` directory |
| Tools not working | Make sure Docker containers are running: `docker-compose up -d` |
| Knowledge base empty | Run `python -m src.rag.embed_catalog --reset` |
| MCP tools timing out | Start MCP servers first, set `MCP_ENABLED=True` in `.env` |

## Key Concepts Covered
- Chainlit `@cl.on_message` and `@cl.on_chat_start` lifecycle
- `@cl.step` for tool call visualization
- `cl.Action` and `@cl.action_callback` for interactive buttons
- `cl.user_session` for multi-turn context persistence
- Structured markdown rendering in chat messages
