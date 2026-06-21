# Day 9: Multi-Agent Orchestration (eComBot v6)

## Overview
We transform the single-agent eComBot into a multi-agent system with an Orchestrator that routes user queries to specialized Support and Sales agents.

## Learning Objectives
- Multi-agent architecture with Google ADK sub_agents
- Intent classification and query routing
- Planner-executor flow for mixed queries
- Delegation tracing and observability

## Architecture

```
User Query
    │
    ▼
┌─────────────┐
│ Orchestrator │──── Intent Classification
└──────┬──────┘
       │
  ┌────┴─────┐
  ▼          ▼
┌──────┐  ┌──────┐
│Support│  │Sales │
│Agent  │  │Agent │
└──────┘  └──────┘
  │          │
  ▼          ▼
Order     Product
Tools     Tools
+ RAG     + RAG
```

### Routing Logic
| Intent | Agent | Signals |
|--------|-------|---------|
| Support | Support Agent | order, track, cancel, return, refund, shipping, complaint |
| Sales | Sales Agent | recommend, compare, buy, price, specs, budget |
| Mixed | Support → Sales | Both support AND sales signals detected |
| Greeting | Orchestrator | hi, hello, thanks, what can you do |

## Files Created/Modified

### `orchestrator.py`
- **Path**: `src/agents/orchestrator.py`
- **Purpose**: Central coordinator agent with sub_agents list
- **Key Components**: Intent classifier, ADK sub_agents delegation, tracing

### `orchestrator_instructions.txt`
- **Path**: `src/agents/orchestrator_instructions.txt`
- **Purpose**: System prompt defining delegation rules

### `support_instructions_v2.txt` / `sales_instructions_v2.txt`
- **Path**: `src/agents/`
- **Purpose**: Refined prompts scoping each agent to its domain only

### `tracing.py`
- **Path**: `src/agents/tracing.py`
- **Purpose**: `OrchestrationTracer` class for logging routing decisions

## How to Run / Test

### Running the Orchestrator
```bash
cd ecombot
python -m src.agents.orchestrator
```

You will see:
```
==================================================
 eComBot v6 — Multi-Agent Orchestrator
==================================================
 Agents: Orchestrator → Support | Sales
==================================================
Type 'exit' to quit, 'trace' to view trace report

You:
```

### Test Case 1: Support Routing
- **Input**: "Where is my order ORD-001?"
- **Expected**: Routes to Support Agent, calls get_order_status, returns order details
- **Trace**: `[SUPPORT → support_agent] 1 support signal(s) detected`

### Test Case 2: Sales Routing
- **Input**: "Can you recommend a good pair of headphones?"
- **Expected**: Routes to Sales Agent, searches products/knowledge base
- **Trace**: `[SALES → sales_agent] 1 sales signal(s) detected`

### Test Case 3: Mixed Query
- **Input**: "Check my order ORD-004 and suggest alternative products"
- **Expected**: Routes to both agents — order status first, then product suggestions
- **Trace**: `[MIXED → support_agent → sales_agent]`

### Test Case 4: Self-Answer
- **Input**: "Hello! What can you help me with?"
- **Expected**: Orchestrator responds directly with capabilities list
- **Trace**: `[SELF → orchestrator]`

### Viewing Trace Report
Type `trace` during chat to see the full delegation history.

## Key Concepts Covered
- ADK `sub_agents` for automatic agent delegation
- Pattern-based intent classification
- Orchestration tracing for debugging
- Agent scope separation (support vs sales)
