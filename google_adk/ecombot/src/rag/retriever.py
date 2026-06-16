"""Retrieve relevant chunks from the ChromaDB knowledge base."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

# project path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import chromadb

from config.settings import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Query the ChromaDB knowledge base and return relevant chunks."""

    def __init__(self) -> None:
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    def _ensure_collection(self) -> chromadb.Collection:
        """Lazily connect to ChromaDB and get the collection."""
        if self._collection is not None:
            return self._collection
        try:
            self._client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
            self._collection = self._client.get_collection(name=CHROMA_COLLECTION_NAME)
            return self._collection
        except Exception as exc:
            logger.exception("Failed to connect to ChromaDB collection")
            raise RuntimeError("Knowledge base is not available.") from exc

    def retrieve(
        self,
        query: str,
        n_results: int = 3,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the top matching chunks for a query.

        Each result dict contains:
            - text: the chunk text
            - metadata: the chunk metadata
            - distance: the similarity distance (lower = more similar)
        """
        if not query or not query.strip():
            return []

        try:
            collection = self._ensure_collection()
        except RuntimeError:
            return []

        query_params: dict[str, Any] = {
            "query_texts": [query.strip()],
            "n_results": min(n_results, collection.count()) if collection.count() > 0 else n_results,
        }
        if where:
            query_params["where"] = where

        try:
            results = collection.query(**query_params)
        except Exception:
            logger.exception("ChromaDB query failed")
            return []

        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        chunks: list[dict[str, Any]] = []
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [None] * len(docs)

        for doc, meta, dist in zip(docs, metas, distances):
            chunks.append({
                "text": doc,
                "metadata": meta or {},
                "distance": dist,
            })

        return chunks

    def retrieve_formatted(self, query: str, n_results: int = 3) -> str:
        """Return retrieved chunks as a formatted context string for the agent."""
        chunks = self.retrieve(query, n_results=n_results)
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "unknown")
            section = chunk["metadata"].get("section", "general")
            distance = chunk.get("distance")
            dist_str = f" (relevance: {1 - distance:.2f})" if distance is not None else ""
            context_parts.append(
                f"[Source {i}: {source} / {section}{dist_str}]\n{chunk['text']}"
            )

        return "\n\n---\n\n".join(context_parts)


# Singleton instance
_retriever: KnowledgeRetriever | None = None


def get_retriever() -> KnowledgeRetriever:
    """Get or create the singleton retriever."""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


# -----------------------------------------------------------
# CLI test
# -----------------------------------------------------------
if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the return policy?"
    retriever = KnowledgeRetriever()
    print(f"\nQuery: {query}\n")
    results = retriever.retrieve(query, n_results=3)
    if not results:
        print("No results found. Have you run embed_catalog.py first?")
    else:
        for i, r in enumerate(results, 1):
            dist = r.get("distance")
            print(f"--- Result {i} (distance: {dist:.4f}) ---")
            print(f"Source: {r['metadata'].get('source')} / {r['metadata'].get('section')}")
            print(f"Text: {r['text'][:200]}...")
            print()
