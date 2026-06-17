# Day 4: Multi-Agent Architecture

## Overview
We transform our single agent into an orchestrator-based system containing specialized sub-agents. The main agent serves as the support point-of-contact and can invoke different instructions for sales or product information if needed.

## Learning Objectives
- Designing a multi-agent hierarchy.
- Providing independent system instructions per specialized role.
- Exposing a unified frontend via a Root agent.

## Architecture
- **Support Agent**: Handles cancellations, order status, and orchestration.
- **Product Agent**: Specifically tuned for deep product feature comparisons.
- **Sales Agent**: Persuasive agent restricted to upselling and product recommendations.

## Files Created/Modified

### `sales_agent.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/sales_agent.py`
- **Purpose**: Standalone sales persona experiment.
- **Key Components**: Uses `sales_instructions_v1.txt`.

### `support_agent.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/support_agent.py`
- **Purpose**: The main orchestrator/root agent integrating all tools.
- **Key Components**: Unifies the tool list `[get_order_status, cancel_order, lookup_product, search_knowledge_base]`.

## How to Run / Test

### Starting the Agent
1. Ensure you are in the project root directory.
2. Run the support orchestrator agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Support Tool Routing**
- **User Input**: "I want to cancel order ORD-004."
- **Expected Outcome**: The agent routes the intent to the `cancel_order` tool and processes the cancellation successfully.

**Test Case 2: Product Tool Routing**
- **User Input**: "Do you have any 4K Webcams in stock?"
- **Expected Outcome**: The agent uses the `lookup_product` tool to search the database and returns the specs and availability for the 4K Webcam.

## Key Concepts Covered
- Tool routing.
- Multi-agent topologies (Orchestrator vs flat).
