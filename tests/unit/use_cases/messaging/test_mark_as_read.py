"""Unit tests for MarkAsReadUseCase."""

import pytest

from src.adapters.redis.read_receipt_store import ReadReceiptStore
from src.use_cases.messaging.mark_as_read import MarkAsReadUseCase


@pytest.fixture
def store():
    return ReadReceiptStore()


@pytest.fixture
def use_case(store):
    return MarkAsReadUseCase(read_receipt_store=store)


class TestMarkAsReadUseCase:
    @pytest.mark.asyncio
    async def test_marks_message_as_read(self, use_case, store):
        await use_case.execute(
            user_id="user-1",
            channel_id="chan-1",
            message_id="msg-abc",
        )
        last_read = await store.get_last_read("user-1", "chan-1")
        assert last_read == "msg-abc"

    @pytest.mark.asyncio
    async def test_overwrites_previous_read_position(self, use_case, store):
        await use_case.execute(user_id="user-1", channel_id="chan-1", message_id="msg-001")
        await use_case.execute(user_id="user-1", channel_id="chan-1", message_id="msg-002")
        last_read = await store.get_last_read("user-1", "chan-1")
        assert last_read == "msg-002"

    @pytest.mark.asyncio
    async def test_different_users_tracked_independently(self, use_case, store):
        await use_case.execute(user_id="user-A", channel_id="chan-1", message_id="msg-A")
        await use_case.execute(user_id="user-B", channel_id="chan-1", message_id="msg-B")
        assert await store.get_last_read("user-A", "chan-1") == "msg-A"
        assert await store.get_last_read("user-B", "chan-1") == "msg-B"

    @pytest.mark.asyncio
    async def test_different_channels_tracked_independently(self, use_case, store):
        await use_case.execute(user_id="user-1", channel_id="chan-A", message_id="msg-X")
        await use_case.execute(user_id="user-1", channel_id="chan-B", message_id="msg-Y")
        assert await store.get_last_read("user-1", "chan-A") == "msg-X"
        assert await store.get_last_read("user-1", "chan-B") == "msg-Y"

    @pytest.mark.asyncio
    async def test_no_read_receipt_before_execute(self, store):
        last_read = await store.get_last_read("user-1", "chan-1")
        assert last_read is None
