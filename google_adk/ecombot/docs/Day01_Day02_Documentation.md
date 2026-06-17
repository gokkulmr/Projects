# Day 1 & 2: Project Foundation & Product Agent

## Overview
This phase establishes the project foundation and creates the initial single-turn product AI agent. We also focus heavily on prompt engineering, controlling the scope of the agent to stay within the bounds of a customer support persona without hallucinating.

## Learning Objectives
- Setting up the Google ADK project skeleton.
- Using `dotenv` and `pydantic-settings` to securely manage configuration.
- Building the first ADK `LlmAgent` using a LiteLLM model via OpenRouter.
- Experimenting with System Instructions to control tone and scope.

## Architecture
The system consists of a simple `Runner` that runs an `LlmAgent`. There are no persistent tools or multi-turn sessions yet; it's a foundation to confirm basic connectivity to the OpenRouter Gemini endpoints.

## Files Created/Modified

### `.env`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/.env`
- **Purpose**: Defines secret tokens.
- **Key Components**: `OPENROUTER_API_KEY`, Redis connection vars, Postgres connection vars.

### `settings.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/config/settings.py`
- **Purpose**: Centralized configuration management.
- **Key Components**: Helper functions `_env`, `_env_int`, `_env_bool`. Exposes database DSNs and API URLs.

### `product_agent.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/product_agent.py`
- **Purpose**: A standalone product-info agent experiment.
- **Key Components**: `ask_ecom()` async function, CLI loop.

### `support_instructions_v1.txt`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/support_instructions_v1.txt`
- **Purpose**: A robust system prompt specifying available tools, strict guardrails, out-of-scope behaviors.

## How to Run / Test

### Starting the Agent
1. Ensure your `.env` file contains a valid `OPENROUTER_API_KEY`.
2. Open a terminal and run the agent:
   ```bash
   python src/agents/product_agent.py
   ```

### Verification Test Cases

**Test Case 1: In-Scope Product Inquiry**
- **User Input**: "What are the specs for the Wireless Headphones?"
- **Expected Outcome**: The agent provides a detailed answer about the headphones, maintaining a professional customer support persona.

**Test Case 2: Out-of-Scope Query**
- **User Input**: "Can you write a python script to sort an array?"
- **Expected Outcome**: The agent should refuse to answer and state that it can only assist with e-commerce customer support questions.

## Key Concepts Covered
- LiteLLM and OpenRouter configuration.
- Google ADK `Runner` and `LlmAgent`.
- System instructions and roleplay constraints.
