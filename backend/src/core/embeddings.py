"""Embedding generation for vector search."""

import httpx

from src.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


async def generate_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector for the given text using OpenAI API.

    Returns None if no API key is configured.
    """
    if not settings.openai_api_key:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]] | None:
    """Generate embeddings for multiple texts in a single API call.

    Returns None if no API key is configured.
    """
    if not settings.openai_api_key or not texts:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": EMBEDDING_MODEL, "input": texts},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # Sort by index to ensure order matches input
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
