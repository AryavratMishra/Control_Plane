from __future__ import annotations

import logging
from typing import Optional
import json
import math

logger = logging.getLogger(__name__)

# Simple in-memory vector store for demo (used when pgvector not available)
_mock_chunks: list[dict] = []


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def add_mock_chunks(chunks: list[dict]) -> None:
    """Add chunks to in-memory store (used in demo mode)."""
    _mock_chunks.extend(chunks)


def _keyword_similarity(query: str, text: str) -> float:
    """Simple keyword overlap scoring as fallback."""
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())
    if not query_words:
        return 0.0
    overlap = query_words & text_words
    return len(overlap) / len(query_words)


async def retrieve_evidence(
    query: str,
    db=None,
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[dict]:
    """
    Retrieve relevant evidence chunks for a query.
    Uses pgvector if embeddings available, otherwise keyword similarity on mock chunks.
    """
    results: list[dict] = []

    # Try DB retrieval if session provided
    if db is not None:
        try:
            from sqlalchemy import select, text
            from app.db.models import RetrievalChunk, TrustedDocument

            # Keyword-based retrieval from DB (simple approach without embeddings)
            query_words = query.lower().split()
            stmt = (
                select(RetrievalChunk, TrustedDocument.name, TrustedDocument.trust_level)
                .join(TrustedDocument)
                .limit(50)
            )
            result = await db.execute(stmt)
            rows = result.all()

            scored = []
            for chunk, doc_name, trust_level in rows:
                score = _keyword_similarity(query, chunk.content)
                if score >= min_score:
                    scored.append({
                        "content": chunk.content,
                        "source": doc_name,
                        "trust_level": trust_level,
                        "score": score,
                        "metadata": chunk.extra_metadata or {},
                    })

            scored.sort(key=lambda x: x["score"], reverse=True)
            results = scored[:top_k]
        except Exception as e:
            logger.warning(f"DB retrieval failed: {e}")

    # Fall back to in-memory mock chunks
    if not results and _mock_chunks:
        scored = []
        for chunk in _mock_chunks:
            score = _keyword_similarity(query, chunk.get("content", ""))
            if score >= min_score:
                scored.append({**chunk, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:top_k]

    return results
