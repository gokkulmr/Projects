"""Embed product catalog and FAQ data into ChromaDB for RAG retrieval.

Usage:
    python -m src.rag.embed_catalog          # index everything
    python -m src.rag.embed_catalog --reset   # wipe + re-index
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# project path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import chromadb

from config.settings import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# -----------------------------------------------------------
# Chunking helpers
# -----------------------------------------------------------
def _product_chunks(products: list[dict]) -> list[tuple[str, dict]]:
    """Convert each product into one or more text chunks with metadata."""
    chunks: list[tuple[str, dict]] = []
    for p in products:
        pid = p.get("product_id", "unknown")
        name = p.get("name", "Unknown product")
        category = p.get("category", "General")

        # Main description chunk
        desc_parts = [
            f"Product: {name} ({pid})",
            f"Category: {category}",
            f"Price: ₹{p['price']}" if p.get("price") else "Price: Not available",
            f"Description: {p.get('description', 'N/A')}",
        ]
        if p.get("specs"):
            specs_text = ", ".join(f"{k}: {v}" for k, v in p["specs"].items())
            desc_parts.append(f"Specifications: {specs_text}")
        if p.get("in_box"):
            desc_parts.append(f"In the box: {', '.join(p['in_box'])}")
        chunks.append((
            "\n".join(desc_parts),
            {"source": "products.json", "product_id": pid, "section": "description", "doc_type": "product"},
        ))

        # Warranty chunk
        if p.get("warranty"):
            chunks.append((
                f"Warranty for {name} ({pid}): {p['warranty']}",
                {"source": "products.json", "product_id": pid, "section": "warranty", "doc_type": "product"},
            ))

        # Shipping chunk
        if p.get("shipping"):
            chunks.append((
                f"Shipping for {name} ({pid}): {p['shipping']}",
                {"source": "products.json", "product_id": pid, "section": "shipping", "doc_type": "product"},
            ))

        # Return policy chunk
        if p.get("return_policy"):
            chunks.append((
                f"Return policy for {name} ({pid}): {p['return_policy']}",
                {"source": "products.json", "product_id": pid, "section": "return_policy", "doc_type": "product"},
            ))

    return chunks


def _faq_chunks(faqs: list[dict]) -> list[tuple[str, dict]]:
    """Convert each FAQ entry into a text chunk with metadata."""
    chunks: list[tuple[str, dict]] = []
    for faq in faqs:
        faq_id = faq.get("id", "unknown")
        question = faq.get("question", "")
        answer = faq.get("answer", "")
        category = faq.get("category", "general")
        text = f"Q: {question}\nA: {answer}"
        chunks.append((
            text,
            {"source": "faq.json", "faq_id": faq_id, "section": category, "doc_type": "faq"},
        ))
    return chunks


# -----------------------------------------------------------
# Indexing
# -----------------------------------------------------------
def index_knowledge_base(reset: bool = False) -> int:
    """Load products.json and faq.json, chunk them, and store in ChromaDB.

    Returns the total number of chunks indexed.
    """
    products_path = DATA_DIR / "products.json"
    faq_path = DATA_DIR / "faq.json"

    if not products_path.exists():
        raise FileNotFoundError(f"Products file not found: {products_path}")
    if not faq_path.exists():
        raise FileNotFoundError(f"FAQ file not found: {faq_path}")

    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    with open(faq_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    all_chunks = _product_chunks(products) + _faq_chunks(faqs)

    logger.info("Total chunks to index: %d", len(all_chunks))

    # Connect to local persistent ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))

    if reset:
        try:
            client.delete_collection(CHROMA_COLLECTION_NAME)
            logger.info("Deleted existing collection: %s", CHROMA_COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "eComBot knowledge base — products and FAQ"},
    )

    # Prepare batch data
    ids = []
    documents = []
    metadatas = []
    for i, (text, meta) in enumerate(all_chunks):
        chunk_id = f"{meta.get('doc_type', 'doc')}_{meta.get('product_id', meta.get('faq_id', 'unknown'))}_{meta.get('section', 'general')}_{i}"
        ids.append(chunk_id)
        documents.append(text)
        metadatas.append(meta)

    # Upsert in batches of 100
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    logger.info("Indexed %d chunks into collection '%s'", len(ids), CHROMA_COLLECTION_NAME)
    logger.info("Collection now has %d documents", collection.count())
    return len(ids)


# -----------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------
if __name__ == "__main__":
    reset = "--reset" in sys.argv
    try:
        count = index_knowledge_base(reset=reset)
        print(f"\nSuccessfully indexed {count} chunks into ChromaDB.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
