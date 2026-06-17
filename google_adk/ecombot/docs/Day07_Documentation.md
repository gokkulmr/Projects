# Day 7: LLM Gateway with LiteLLM Proxy

## Overview
We introduce the LiteLLM proxy gateway to route requests intelligently between a fast, cheap model (for simple queries) and a slower, more capable model (for deep reasoning or complex multi-step queries). We also implement fallback behavior in case a provider endpoint is down.

## Learning Objectives
- Understanding the benefits of LLM proxies.
- Writing LiteLLM `litellm_config.yaml` files.
- Implementing a query router to classify query complexity.
- Modifying Google ADK to point to local proxy endpoints instead of the direct provider API.

## Architecture
- ADK's `LlmAgent` calls `http://localhost:4000/v1/chat/completions`.
- A `QueryRouter` examines the user input and tags it with a routing hint.
- LiteLLM interprets the tag and delegates to the appropriate underlying model (e.g., `gemini-2.0-flash` vs `gemini-2.5-flash`).
- If a model is rate-limited or fails, LiteLLM automatically retries using a fallback chain.

## Files Created/Modified

### `litellm_config.yaml`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/gateway/litellm_config.yaml`
- **Purpose**: Configure the `fast-faq` and `deep-support` routes.
- **Key Components**: Defines the OpenRouter keys and the fallback arrays.

### `router.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/gateway/router.py`
- **Purpose**: Analyzes the input string for complexity heuristics.
- **Key Components**: `QueryRouter` class, keyword checking.

### `support_agent.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/support_agent.py`
- **Purpose**: Wires the router classification into the chat loop.
- **Key Components**: Now uses `LITELLM_PROXY_ENABLED` flag to determine model initialization.

## How to Run / Test

### Starting the Gateway
1. Ensure your `.env` contains `OPENROUTER_API_KEY` and `LITELLM_PROXY_ENABLED=True`.
2. Open a terminal and start the proxy on port 4000:
   ```bash
   litellm --config src/gateway/litellm_config.yaml --port 4000
   ```
3. Open a second terminal and start the support agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Fast-FAQ Routing**
- **User Input**: "How long does shipping take?"
- **Expected Outcome**: The `QueryRouter` tags this as simple. You should see a log `[fast-faq route selected]` in the terminal. The proxy fulfills the request using the cheaper, faster model.

**Test Case 2: Deep-Support Routing**
- **User Input**: "I received my order ORD-001 but the box is completely smashed and I need a replacement immediately because it's a gift."
- **Expected Outcome**: The `QueryRouter` tags this as a complex complaint. You should see `[deep-support route selected]` logged, and the proxy uses the more capable reasoning model to process the multi-step return policy logic.

## Key Concepts Covered
- Intelligent Model Routing.
- Latency and cost optimization.
- High-availability and failover with LLM proxies.
