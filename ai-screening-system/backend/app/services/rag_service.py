"""
app/services/rag_service.py
RAG pipeline:
  1. Ingestion   – chunk role-specific PDFs, embed, store in ChromaDB
  2. Retrieval   – build query from resume skills + role, retrieve top-k chunks
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Singleton embedding model ─────────────────────────────────────────────────
_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


# ── ChromaDB client ───────────────────────────────────────────────────────────
_chroma_client: chromadb.PersistentClient | None = None


def get_chroma() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def _collection_name(role: str) -> str:
    return role.lower().replace(" ", "_").replace("/", "_")


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Simple sliding-window chunker (word-boundary aware)."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i : i + size])
        chunks.append(chunk)
        i += size - overlap
    return [c for c in chunks if len(c.strip()) > 50]


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest_document(role: str, filepath: str | Path) -> int:
    """
    Read a PDF/TXT knowledge-base document, chunk it, embed, upsert to Chroma.
    Returns number of chunks ingested.
    """
    from pypdf import PdfReader

    filepath = Path(filepath)
    if filepath.suffix.lower() == ".pdf":
        reader = PdfReader(filepath)
        raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    else:
        raw = filepath.read_text(encoding="utf-8", errors="replace")

    if not raw.strip():
        logger.warning("Empty document: %s", filepath)
        return 0

    chunks = _chunk_text(raw, settings.chunk_size, settings.chunk_overlap)
    embedder = get_embedder()
    client = get_chroma()
    collection = client.get_or_create_collection(
        name=_collection_name(role),
        metadata={"hnsw:space": "cosine"},
    )

    embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()
    ids = [f"{filepath.stem}__chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filepath.name, "role": role, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    logger.info("Ingested %d chunks for role '%s' from '%s'", len(chunks), role, filepath.name)
    return len(chunks)


def ingest_all_knowledge_base() -> dict[str, int]:
    """
    Walk the knowledge_base/ directory.
    Expected layout:
        knowledge_base/
            ai_ml_engineer/
                ml_book.pdf
                ...
            backend_engineer/
                ...
    Returns dict of {role: chunk_count}.
    """
    kb_dir = Path(settings.knowledge_base_dir)
    summary: dict[str, int] = {}
    if not kb_dir.exists():
        logger.warning("Knowledge base directory not found: %s", kb_dir)
        return summary

    for role_dir in kb_dir.iterdir():
        if not role_dir.is_dir():
            continue
        role_name = role_dir.name.replace("_", " ").title()
        total = 0
        for doc in role_dir.glob("**/*"):
            if doc.suffix.lower() in (".pdf", ".txt", ".md"):
                total += ingest_document(role_name, doc)
        summary[role_name] = total
    return summary


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_context(
    role: str,
    skills: dict[str, list[str]],
    topic_hint: str = "",
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Build a semantic query from the candidate's skills + role + optional topic,
    retrieve top_k chunks from the role's ChromaDB collection.

    Returns list of dicts: {text, source, score}
    """
    # Build rich query
    all_skills = []
    for cat_skills in skills.values():
        if isinstance(cat_skills, list):
            all_skills.extend(cat_skills)

    query_parts = [f"Interview questions for {role}"]
    if all_skills:
        query_parts.append(f"Concepts related to: {', '.join(all_skills[:15])}")
    if topic_hint:
        query_parts.append(topic_hint)
    query = ". ".join(query_parts)

    embedder = get_embedder()
    client = get_chroma()
    col_name = _collection_name(role)

    try:
        collection = client.get_collection(col_name)
    except Exception:
        logger.warning("No collection found for role '%s'. Using fallback context.", role)
        return _fallback_context(role)

    q_embedding = embedder.encode([query]).tolist()
    results = collection.query(
        query_embeddings=q_embedding,
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "score": round(1 - dist, 4),  # cosine similarity
        })
    return chunks


def _fallback_context(role: str) -> list[dict[str, Any]]:
    """Return generic context if no KB is available (graceful degradation)."""
    templates = {
        "AI/ML Engineer": (
            "Machine learning fundamentals include supervised learning (regression, "
            "classification), unsupervised learning (clustering, dimensionality reduction), "
            "and reinforcement learning. Key algorithms: linear regression, decision trees, "
            "random forests, gradient boosting, neural networks. Deep learning covers CNNs "
            "for vision tasks and Transformers for NLP. RAG combines retrieval systems with "
            "generative models to ground responses in factual context."
        ),
        "Backend Engineer": (
            "Backend engineering involves designing RESTful and GraphQL APIs, database "
            "schema design (normalisation, indexing, query optimisation), distributed systems "
            "concepts (CAP theorem, eventual consistency), caching strategies (Redis, CDN), "
            "message queues (Kafka, RabbitMQ), and microservices architecture. "
            "Authentication via JWT/OAuth2 and security best practices are essential."
        ),
    }
    text = templates.get(role, f"Core concepts relevant to {role} engineering role.")
    return [{"text": text, "source": "fallback", "score": 0.5}]


def kb_status() -> dict[str, Any]:
    """Return info about what's indexed in ChromaDB."""
    client = get_chroma()
    cols = client.list_collections()
    roles = [c.name.replace("_", " ").title() for c in cols]
    total = sum(c.count() for c in cols)
    return {
        "roles_indexed": roles,
        "total_chunks": total,
        "embedding_model": settings.embedding_model,
    }
