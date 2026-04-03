"""Unit tests for Redis token blacklist adapter."""

from unittest.mock import AsyncMock

import pytest

from src.adapters.redis.token_blacklist import TokenBlacklist


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.exists = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def blacklist(mock_redis):
    return TokenBlacklist(redis_client=mock_redis)


class TestTokenBlacklist:
    @pytest.mark.asyncio
    async def test_blacklist_calls_redis_set_with_prefix_and_ttl(self, blacklist, mock_redis):
        await blacklist.blacklist("my-token", 300)
        mock_redis.set.assert_called_once_with("blacklist:my-token", "1", ex=300)

    @pytest.mark.asyncio
    async def test_is_blacklisted_returns_true_when_key_exists(self, blacklist, mock_redis):
        mock_redis.exists = AsyncMock(return_value=1)
        result = await blacklist.is_blacklisted("my-token")
        assert result is True
        mock_redis.exists.assert_called_once_with("blacklist:my-token")

    @pytest.mark.asyncio
    async def test_is_blacklisted_returns_false_when_key_missing(self, blacklist, mock_redis):
        mock_redis.exists = AsyncMock(return_value=0)
        result = await blacklist.is_blacklisted("unknown-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_uses_correct_key_prefix(self, blacklist, mock_redis):
        token = "abc123"
        await blacklist.blacklist(token, 60)
        call_key = mock_redis.set.call_args[0][0]
        assert call_key == f"blacklist:{token}"

    @pytest.mark.asyncio
    async def test_is_blacklisted_uses_correct_key_prefix(self, blacklist, mock_redis):
        token = "xyz789"
        await blacklist.is_blacklisted(token)
        call_key = mock_redis.exists.call_args[0][0]
        assert call_key == f"blacklist:{token}"

    @pytest.mark.asyncio
    async def test_blacklist_different_tokens_use_distinct_keys(self, blacklist, mock_redis):
        await blacklist.blacklist("token-a", 100)
        await blacklist.blacklist("token-b", 200)
        calls = mock_redis.set.call_args_list
        keys = [c[0][0] for c in calls]
        assert "blacklist:token-a" in keys
        assert "blacklist:token-b" in keys
        assert keys[0] != keys[1]
