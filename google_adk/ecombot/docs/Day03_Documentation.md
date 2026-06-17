# Day 3: Multi-Turn Conversation & Session Management

## Overview
This phase adds memory to the agent so it can handle multi-turn conversations. The agent remembers customer context (such as previously mentioned Order IDs) throughout the session.

## Learning Objectives
- Understanding Google ADK `SessionService`.
- Using `InMemorySessionService` to track state locally.
- Accessing `ToolContext.state` from within an ADK `@tool`.

## Architecture
The `Runner` uses an `InMemorySessionService` to map `user_id` and `session_id` to an internal memory object. The LLM can contextually parse pronouns like "What is the status of *that* order?" by remembering the previously discussed order.

## Files Created/Modified

### `sessions.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/sessions.py`
- **Purpose**: Wraps the ADK runner with an in-memory chat session class.
- **Key Components**: `ChatSession` class.

### `order_tools.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/tools/order_tools.py`
- **Purpose**: Defines tools that the agent can execute.
- **Key Components**: `get_order_status` which writes `last_order_id` to `tool_context.state`.

## How to Run / Test

### Starting the Agent
1. Ensure you are in the project root directory.
2. Run the support agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Session Memory Verification**
- **Turn 1 (User Input)**: "Can you look up order ORD-001?"
- **Turn 1 (Expected)**: The agent calls `get_order_status` and returns details for Priya Sharma's order.
- **Turn 2 (User Input)**: "Actually, can you cancel that order?"
- **Turn 2 (Expected)**: The agent remembers `ORD-001` from the session state and attempts to cancel it using the `cancel_order` tool, rather than asking you for the order ID again.

## Key Concepts Covered
- In-memory state tracking.
- The ADK `ToolContext` object.
- Stateful multi-turn loops.
