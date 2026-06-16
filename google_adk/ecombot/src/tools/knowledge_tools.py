"""Knowledge base search tool backed by ChromaDB RAG."""

from __future__ import annotations

import os
import sys
from typing import Any

# project path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from google.adk.tools import ToolContext  # type: ignore
    from google.adk.tools import tool  # type: ignore
except Exception:
    def tool(func):  # type: ignore
        return func

    class ToolContext:  # type: ignore
        state: dict[str, Any]


@tool
def search_knowledge_base(query: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """Search the product catalog and FAQ knowledge base for relevant information.

    Use this tool when a customer asks about:
    - Product specifications, features, or details
    - Warranty information
    - Return policy
    - Shipping options and timelines
    - Payment methods
    - General FAQ questions about the store
    - Any question that requires factual knowledge about our products or policies
    """
    if not query or len(query.strip()) < 3:
        return {
            "ok": False,
            "error": "Search query is too short. Please provide a more specific question.",
        }

    try:
        from rag.retriever import get_retriever
        retriever = get_retriever()
        chunks = retriever.retrieve(query.strip(), n_results=3)
    except Exception:
        return {
            "ok": False,
            "error": "Knowledge base is temporarily unavailable. Please try again later.",
        }

    if not chunks:
        return {
            "ok": False,
            "error": f"No relevant information found in the knowledge base for: '{query}'. I don't have enough information to answer this question accurately.",
            "query": query,
        }

    # Check if the results are actually relevant (distance threshold)
    # ChromaDB default distance is L2; lower = more similar
    relevant_chunks = []
    for chunk in chunks:
        dist = chunk.get("distance")
        # Filter out very distant matches (threshold depends on embedding model)
        if dist is not None and dist > 1.5:
            continue
        relevant_chunks.append({
            "text": chunk["text"],
            "source": chunk["metadata"].get("source", chunk["metadata"].get("source_file", "unknown")),
            "section": chunk["metadata"].get("section", "general"),
            "doc_type": chunk["metadata"].get("doc_type", "unknown"),
        })

    if not relevant_chunks:
        return {
            "ok": False,
            "error": f"The knowledge base does not contain confident information about: '{query}'. I cannot answer this question without risking inaccuracy.",
            "query": query,
        }

    if tool_context is not None:
        tool_context.state["last_intent"] = "knowledge_search"
        tool_context.state["last_lookup_key"] = query

    return {
        "ok": True,
        "query": query,
        "results": relevant_chunks,
        "note": "Answer ONLY based on the information provided above. Do not add information that is not present in these results.",
    }
