"""Unit tests for GetOnlineUsersUseCase."""

import pytest

from src.adapters.redis.presence_store import PresenceStore
from src.use_cases.presence.get_online_users import GetOnlineUsersUseCase


@pytest.fixture
def store():
    return PresenceStore()


@pytest.fixture
def use_case(store):
    return GetOnlineUsersUseCase(presence_store=store)


class TestGetOnlineUsersUseCase:
    @pytest.mark.asyncio
    async def test_empty_channel_returns_empty_list(self, use_case):
        result = await use_case.execute(channel_id="chan-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_online_user_in_channel_returned(self, use_case, store):
        await store.set_online("user-1", "chan-1")
        result = await use_case.execute(channel_id="chan-1")
        assert "user-1" in result

    @pytest.mark.asyncio
    async def test_offline_user_not_returned(self, use_case, store):
        await store.set_online("user-1", "chan-1")
        await store.set_offline("user-1")
        result = await use_case.execute(channel_id="chan-1")
        assert "user-1" not in result

    @pytest.mark.asyncio
    async def test_user_in_different_channel_not_returned(self, use_case, store):
        await store.set_online("user-1", "chan-other")
        result = await use_case.execute(channel_id="chan-1")
        assert "user-1" not in result

    @pytest.mark.asyncio
    async def test_multiple_users_in_channel_all_returned(self, use_case, store):
        await store.set_online("user-A", "chan-1")
        await store.set_online("user-B", "chan-1")
        await store.set_online("user-C", "chan-2")
        result = await use_case.execute(channel_id="chan-1")
        assert set(result) == {"user-A", "user-B"}

    @pytest.mark.asyncio
    async def test_user_online_in_multiple_channels_appears_in_both(self, use_case, store):
        await store.set_online("user-1", "chan-1")
        await store.set_online("user-1", "chan-2")
        result_1 = await use_case.execute(channel_id="chan-1")
        result_2 = await use_case.execute(channel_id="chan-2")
        assert "user-1" in result_1
        assert "user-1" in result_2
