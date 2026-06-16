"""PDF ingestion pipeline for Day 06 — extract, chunk, and index PDF content.

Usage:
    python -m src.rag.pdf_ingestor data/ecom_faq.pdf          # index a PDF
    python -m src.rag.pdf_ingestor data/ecom_faq.pdf --reset   # wipe + re-index
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# project path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import chromadb
from pypdf import PdfReader

from config.settings import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -----------------------------------------------------------
# Heading detection
# -----------------------------------------------------------
_HEADING_PATTERN = re.compile(
    r"^(?:\d+[\.\)]\s*|#{1,4}\s+|[A-Z][A-Z\s]{5,}$)",
    re.MULTILINE,
)


def _detect_section(text: str) -> str:
    """Try to extract a section heading from chunk text."""
    for line in text.split("\n")[:3]:
        line = line.strip()
        if _HEADING_PATTERN.match(line):
            return line[:80]
    return "General"


# -----------------------------------------------------------
# PDF text extraction
# -----------------------------------------------------------
def extract_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Extract text from each page of a PDF.

    Returns a list of dicts with 'page' (1-indexed) and 'text'.
    """
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i, "text": text.strip()})
    return pages


# -----------------------------------------------------------
# Chunking with overlap
# -----------------------------------------------------------
def chunk_pages(
    pages: list[dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split page texts into overlapping chunks.

    Each chunk dict has:
        - text: the chunk text
        - page: source page number
        - section: detected section heading
    """
    chunks: list[dict[str, Any]] = []
    for page_info in pages:
        page_num = page_info["page"]
        text = page_info["text"]

        # Split by paragraph first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk = f"{current_chunk}\n{para}" if current_chunk else para
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "page": page_num,
                        "section": _detect_section(current_chunk),
                    })
                # Start new chunk with overlap from previous
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = f"{overlap_text}\n{para}"
                else:
                    current_chunk = para

        # Final chunk for this page
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "page": page_num,
                "section": _detect_section(current_chunk),
            })

    return chunks


# -----------------------------------------------------------
# Indexing
# -----------------------------------------------------------
def index_pdf(
    pdf_path: str | Path,
    document_title: str | None = None,
    reset: bool = False,
    chunk_size: int = 500,
    overlap: int = 50,
) -> int:
    """Extract text from a PDF, chunk it, and store in ChromaDB.

    Returns the number of chunks indexed.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc_title = document_title or pdf_path.stem.replace("_", " ").title()
    source_file = pdf_path.name

    logger.info("Extracting text from: %s", pdf_path)
    pages = extract_pages(pdf_path)
    logger.info("Extracted %d pages", len(pages))

    chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
    logger.info("Created %d chunks (size=%d, overlap=%d)", len(chunks), chunk_size, overlap)

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))

    if reset:
        try:
            client.delete_collection(CHROMA_COLLECTION_NAME)
            logger.info("Deleted existing collection: %s", CHROMA_COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "eComBot knowledge base — products, FAQ, and PDFs"},
    )

    # Prepare batch data
    ids = []
    documents = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"pdf_{source_file}_{chunk['page']}_{i}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "source_file": source_file,
            "document_title": doc_title,
            "section": chunk["section"],
            "page": chunk["page"],
            "doc_type": "pdf",
        })

    # Upsert in batches
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    logger.info("Indexed %d PDF chunks into collection '%s'", len(ids), CHROMA_COLLECTION_NAME)
    logger.info("Collection now has %d total documents", collection.count())
    return len(ids)


# -----------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if not args:
        print("Usage: python -m src.rag.pdf_ingestor <path-to-pdf> [--reset]")
        sys.exit(1)

    pdf_file = args[0]
    do_reset = "--reset" in flags

    try:
        count = index_pdf(pdf_file, reset=do_reset)
        print(f"\nSuccessfully indexed {count} PDF chunks into ChromaDB.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
