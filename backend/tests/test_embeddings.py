"""Tests for the embeddings module."""

from unittest.mock import AsyncMock, patch

import pytest

from src.core.embeddings import generate_embedding, generate_embeddings_batch


@pytest.mark.asyncio
async def test_generate_embedding_no_api_key():
    """Should return None when no OpenAI key is configured."""
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        result = await generate_embedding("test text")
        assert result is None


@pytest.mark.asyncio
async def test_generate_embeddings_batch_no_api_key():
    """Should return None when no OpenAI key is configured."""
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        result = await generate_embeddings_batch(["text1", "text2"])
        assert result is None


@pytest.mark.asyncio
async def test_generate_embeddings_batch_empty_input():
    """Should return None for empty input."""
    with patch("src.core.embeddings.settings") as mock_settings:
        mock_settings.openai_api_key = "test-key"
        result = await generate_embeddings_batch([])
        assert result is None


@pytest.mark.asyncio
async def test_generate_embedding_with_api_key():
    """Should call OpenAI API when key is configured."""
    mock_embedding = [0.1] * 1536

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "data": [{"embedding": mock_embedding, "index": 0}]
    }

    with patch("src.core.embeddings.settings") as mock_settings, \
         patch("src.core.embeddings.httpx.AsyncClient") as MockClient:
        mock_settings.openai_api_key = "test-key"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client_instance

        result = await generate_embedding("test text")

        assert result == mock_embedding
        mock_client_instance.post.assert_called_once()
