"""Local BGE embedding generation for vector search and semantic intent."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from src.core.config import settings

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIMENSIONS = 1024

# BGE retrieval: prefix queries when matching against indexed document/passage vectors.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
_model_lock = asyncio.Lock()


def _load_model() -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


async def _get_model() -> SentenceTransformer:
    global _model
    if _model is not None:
        return _model
    async with _model_lock:
        if _model is None:
            _model = await asyncio.to_thread(_load_model)
    return _model


def _encode_sync(texts: list[str], *, for_query: bool) -> list[list[float]]:
    """Run in a worker thread; loads the model on first use."""
    global _model
    if _model is None:
        _model = _load_model()

    prepared = texts
    if for_query:
        prepared = [f"{BGE_QUERY_PREFIX}{text}" for text in texts]

    vectors = _model.encode(
        prepared,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    if hasattr(vectors, "tolist"):
        return vectors.tolist()
    return [list(row) for row in vectors]


async def generate_embedding(text: str, *, for_query: bool = False) -> list[float] | None:
    """Generate one embedding vector. Returns None when embeddings are disabled or text is empty."""
    if not settings.embeddings_enabled:
        return None
    stripped = text.strip()
    if not stripped:
        return None

    batch = await asyncio.to_thread(_encode_sync, [stripped], for_query=for_query)
    return batch[0]


async def generate_embeddings_batch(
    texts: list[str],
    *,
    for_query: bool = False,
) -> list[list[float]] | None:
    """Generate embeddings for multiple texts (passage/document mode by default)."""
    if not settings.embeddings_enabled or not texts:
        return None

    normalized = [t.strip() or " " for t in texts]
    return await asyncio.to_thread(_encode_sync, normalized, for_query=for_query)
