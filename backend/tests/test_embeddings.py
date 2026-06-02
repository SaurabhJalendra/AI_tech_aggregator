"""Tests for the embeddings module (local BGE)."""

from unittest.mock import patch

import pytest

from src.core.embeddings import (
    EMBEDDING_DIMENSIONS,
    generate_embedding,
    generate_embeddings_batch,
)


@pytest.mark.asyncio
async def test_generate_embedding_disabled():
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = False
        result = await generate_embedding("test text")
        assert result is None


@pytest.mark.asyncio
async def test_generate_embeddings_batch_disabled():
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = False
        result = await generate_embeddings_batch(["text1", "text2"])
        assert result is None


@pytest.mark.asyncio
async def test_generate_embeddings_batch_empty_input():
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        result = await generate_embeddings_batch([])
        assert result is None


@pytest.mark.asyncio
async def test_generate_embedding_returns_vector():
    mock_vector = [0.1] * EMBEDDING_DIMENSIONS

    with patch("src.core.embeddings.settings") as mock_settings, patch(
        "src.core.embeddings.asyncio.to_thread",
        return_value=[mock_vector],  # _encode_sync returns list[list[float]]
    ) as mock_thread:
        mock_settings.embeddings_enabled = True
        result = await generate_embedding("test text", for_query=True)

        assert result == mock_vector
        mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_for_query_flag():
    mock_vectors = [[0.1] * EMBEDDING_DIMENSIONS, [0.2] * EMBEDDING_DIMENSIONS]

    with patch("src.core.embeddings.settings") as mock_settings, patch(
        "src.core.embeddings.asyncio.to_thread",
        return_value=mock_vectors,
    ) as mock_thread:
        mock_settings.embeddings_enabled = True
        result = await generate_embeddings_batch(["a", "b"], for_query=False)

        assert result == mock_vectors
        args, kwargs = mock_thread.call_args
        assert kwargs.get("for_query") is False
