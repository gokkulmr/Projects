# Day 5: RAG (Retrieval-Augmented Generation) with ChromaDB

## Overview
We integrate ChromaDB to store vector embeddings of product specifications and FAQ entries. This allows our agent to answer factual questions grounded in internal documentation without hallucinating.

## Learning Objectives
- Setting up ChromaDB collections.
- Using sentence-transformers to embed text documents.
- Implementing an ADK `@tool` that performs semantic search over the vector store.
- Writing anti-hallucination prompts.

## Architecture
- `products.json` and `faq.json` are parsed into text chunks.
- An ingestor script uses an embedding model to convert them to vectors.
- A `search_knowledge_base` tool queries the vectors using Euclidean distance metrics and passes context back to the LLM.

## Files Created/Modified

### `embed_catalog.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/rag/embed_catalog.py`
- **Purpose**: JSON to ChromaDB indexer. Upserts chunks in batches of 100.
- **Key Components**: Reads `.json` files, chunks by warranty/shipping/returns, embeds text.

### `retriever.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/rag/retriever.py`
- **Purpose**: Queries the vector database.
- **Key Components**: `KnowledgeRetriever` singleton class. Includes `retrieve_formatted` function.

### `knowledge_tools.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/tools/knowledge_tools.py`
- **Purpose**: Defines the `search_knowledge_base` tool available to the Support Agent.
- **Key Components**: Distance threshold filtering to prevent irrelevant data retrieval.

## How to Run / Test

### Starting the Services
1. Ensure your virtual environment has `chromadb` installed.
2. Populate the ChromaDB database with catalog and FAQ vectors:
   ```bash
   python src/rag/embed_catalog.py
   ```
3. Start the support agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Knowledge Retrieval**
- **User Input**: "What is your return policy?"
- **Expected Outcome**: The agent triggers `search_knowledge_base`, retrieves chunks from `faq.json`, and outputs the exact return policy without making up timelines.

**Test Case 2: Hallucination Prevention**
- **User Input**: "Do you offer a 5-year warranty on the mechanical keyboard?"
- **Expected Outcome**: The agent checks the knowledge base, realizes the information contradicts or isn't present, and clarifies the actual warranty period found in the data, refusing to confirm the fake 5-year claim.

## Key Concepts Covered
- Embeddings and Vector Databases.
- Grounding contexts (RAG).
- Metadata-enriched vectors.
