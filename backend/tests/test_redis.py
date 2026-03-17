"""Tests for the Redis caching module."""

from unittest.mock import AsyncMock, patch

import pytest

from src.core.redis import cache_get, cache_set, cache_delete


@pytest.mark.asyncio
async def test_cache_get_no_redis():
    """Should return None when Redis is not available."""
    with patch("src.core.redis.get_redis", return_value=None):
        result = await cache_get("test_key")
        assert result is None


@pytest.mark.asyncio
async def test_cache_set_no_redis():
    """Should return False when Redis is not available."""
    with patch("src.core.redis.get_redis", return_value=None):
        result = await cache_set("test_key", {"data": 1})
        assert result is False


@pytest.mark.asyncio
async def test_cache_delete_no_redis():
    """Should return False when Redis is not available."""
    with patch("src.core.redis.get_redis", return_value=None):
        result = await cache_delete("test_key")
        assert result is False


@pytest.mark.asyncio
async def test_cache_get_with_data():
    """Should return cached data when available."""
    mock_client = AsyncMock()
    mock_client.get.return_value = '{"key": "value"}'

    with patch("src.core.redis.get_redis", return_value=mock_client):
        result = await cache_get("test_key")
        assert result == {"key": "value"}
        mock_client.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_get_miss():
    """Should return None on cache miss."""
    mock_client = AsyncMock()
    mock_client.get.return_value = None

    with patch("src.core.redis.get_redis", return_value=mock_client):
        result = await cache_get("missing_key")
        assert result is None


@pytest.mark.asyncio
async def test_cache_set_success():
    """Should store data and return True."""
    mock_client = AsyncMock()

    with patch("src.core.redis.get_redis", return_value=mock_client):
        result = await cache_set("test_key", {"data": 1}, ttl=600)
        assert result is True
        mock_client.set.assert_called_once()
