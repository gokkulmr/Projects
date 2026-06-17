# eComBot Documentation

Welcome to the documentation for the eComBot Capstone Project. This project is built incrementally over 8+ days to create a production-ready multi-agent AI customer support platform.

## Daily Progress

- **[Day 1 & 2](Day01_Day02_Documentation.md)**: Project Foundation & Product Agent
- **[Day 3](Day03_Documentation.md)**: Multi-Turn Conversation & Session Management
- **[Day 4](Day04_Documentation.md)**: Multi-Agent Architecture
- **[Day 5](Day05_Documentation.md)**: RAG (Retrieval-Augmented Generation) with ChromaDB
- **[Day 6](Day06_Documentation.md)**: Database Integration
- **[Day 7](Day07_Documentation.md)**: LLM Gateway with LiteLLM Proxy
- **[Day 8](Day08_Documentation.md)**: FastMCP & External Integrations

## Architecture Overview

The system architecture features:
- **Google ADK**: Used to define the LLM agents and the Runner loop.
- **LiteLLM Gateway**: Serves as a proxy for OpenRouter to handle routing and fallbacks between different Gemini flash models.
- **FastMCP**: Enables secure connections to external tools and servers to provide mock functionality such as order lookups and product checks.
- **ChromaDB**: Acts as the vector database for performing local RAG on PDF and JSON product/FAQ data.
- **PostgreSQL**: Stores persistent order and product catalog mock data, and full conversation histories.
- **Redis**: Provides short-lived but durable context across user sessions.
