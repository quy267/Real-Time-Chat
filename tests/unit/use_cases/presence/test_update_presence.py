"""Unit tests for UpdatePresenceUseCase."""

import pytest

from src.adapters.redis.presence_store import PresenceStore
from src.use_cases.presence.update_presence import UpdatePresenceUseCase


@pytest.fixture
def store():
    return PresenceStore()


@pytest.fixture
def use_case(store):
    return UpdatePresenceUseCase(presence_store=store)


class TestUpdatePresenceUseCase:
    @pytest.mark.asyncio
    async def test_set_online_marks_user_online(self, use_case, store):
        await use_case.execute(user_id="user-1", online=True)
        assert await store.is_online("user-1") is True

    @pytest.mark.asyncio
    async def test_set_offline_marks_user_offline(self, use_case, store):
        await store.set_online("user-1")
        await use_case.execute(user_id="user-1", online=False)
        assert await store.is_online("user-1") is False

    @pytest.mark.asyncio
    async def test_set_offline_when_already_offline_is_idempotent(self, use_case, store):
        await use_case.execute(user_id="user-1", online=False)
        assert await store.is_online("user-1") is False

    @pytest.mark.asyncio
    async def test_set_online_multiple_users_independent(self, use_case, store):
        await use_case.execute(user_id="user-A", online=True)
        await use_case.execute(user_id="user-B", online=True)
        await use_case.execute(user_id="user-A", online=False)
        assert await store.is_online("user-A") is False
        assert await store.is_online("user-B") is True

    @pytest.mark.asyncio
    async def test_online_then_offline_cycle(self, use_case, store):
        await use_case.execute(user_id="user-1", online=True)
        assert await store.is_online("user-1") is True
        await use_case.execute(user_id="user-1", online=False)
        assert await store.is_online("user-1") is False
