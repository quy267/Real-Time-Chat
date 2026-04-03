"""Unit tests for GetUnreadCountUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.adapters.redis.read_receipt_store import ReadReceiptStore
from src.domain.entities.message import Message
from src.use_cases.messaging.get_unread_count import GetUnreadCountUseCase
from tests.fakes.fake_message_repository import FakeMessageRepository


def _make_message(channel_id: uuid.UUID, offset_seconds: int = 0) -> Message:
    return Message(
        id=uuid.uuid4(),
        content="test",
        channel_id=channel_id,
        user_id=uuid.uuid4(),
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds),
        updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def channel_id():
    return uuid.uuid4()


@pytest.fixture
def store():
    return ReadReceiptStore()


@pytest.fixture
def msg_repo():
    return FakeMessageRepository()


@pytest.fixture
def use_case(store, msg_repo):
    return GetUnreadCountUseCase(read_receipt_store=store, message_repo=msg_repo)


class TestGetUnreadCountUseCase:
    @pytest.mark.asyncio
    async def test_no_read_receipt_all_messages_unread(self, use_case, msg_repo, channel_id):
        for i in range(3):
            await msg_repo.create(_make_message(channel_id, offset_seconds=i))
        count = await use_case.execute(user_id="user-1", channel_id=str(channel_id))
        assert count == 3

    @pytest.mark.asyncio
    async def test_no_read_receipt_empty_channel_returns_zero(self, use_case, channel_id):
        count = await use_case.execute(user_id="user-1", channel_id=str(channel_id))
        assert count == 0

    @pytest.mark.asyncio
    async def test_pivot_not_found_returns_zero(self, use_case, store, msg_repo, channel_id):
        # Store a last-read ID that doesn't exist in message repo
        missing_id = str(uuid.uuid4())
        await store.mark_read("user-1", str(channel_id), missing_id)
        await msg_repo.create(_make_message(channel_id, offset_seconds=0))
        count = await use_case.execute(user_id="user-1", channel_id=str(channel_id))
        assert count == 0

    @pytest.mark.asyncio
    async def test_counts_messages_newer_than_pivot(self, use_case, store, msg_repo, channel_id):
        m1 = _make_message(channel_id, offset_seconds=0)
        m2 = _make_message(channel_id, offset_seconds=10)
        m3 = _make_message(channel_id, offset_seconds=20)
        await msg_repo.create(m1)
        await msg_repo.create(m2)
        await msg_repo.create(m3)

        # User has read up to m1
        await store.mark_read("user-1", str(channel_id), str(m1.id))
        count = await use_case.execute(user_id="user-1", channel_id=str(channel_id))
        # m2 and m3 are newer than m1
        assert count == 2

    @pytest.mark.asyncio
    async def test_all_read_returns_zero_unread(self, use_case, store, msg_repo, channel_id):
        m1 = _make_message(channel_id, offset_seconds=0)
        m2 = _make_message(channel_id, offset_seconds=10)
        await msg_repo.create(m1)
        await msg_repo.create(m2)

        # User has read the latest message
        await store.mark_read("user-1", str(channel_id), str(m2.id))
        count = await use_case.execute(user_id="user-1", channel_id=str(channel_id))
        assert count == 0
