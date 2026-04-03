"""Unit tests for GetThreadRepliesUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.message import Message
from src.domain.entities.thread import Thread
from src.domain.exceptions import EntityNotFoundError
from src.use_cases.threads.get_thread_replies import GetThreadRepliesUseCase
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_thread_repository import FakeThreadRepository


def _make_thread(channel_id: uuid.UUID) -> Thread:
    return Thread(
        id=uuid.uuid4(),
        channel_id=channel_id,
        parent_message_id=uuid.uuid4(),
    )


def _make_reply(thread_id: uuid.UUID, channel_id: uuid.UUID, offset_seconds: int = 0) -> Message:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return Message(
        id=uuid.uuid4(),
        content="reply content",
        channel_id=channel_id,
        user_id=uuid.uuid4(),
        thread_id=thread_id,
        created_at=base + timedelta(seconds=offset_seconds),
        updated_at=base,
    )


@pytest.fixture
def channel_id():
    return uuid.uuid4()


@pytest.fixture
def thread_repo():
    return FakeThreadRepository()


@pytest.fixture
def msg_repo():
    return FakeMessageRepository()


@pytest.fixture
def use_case(thread_repo, msg_repo):
    return GetThreadRepliesUseCase(thread_repo=thread_repo, message_repo=msg_repo)


class TestGetThreadRepliesUseCase:
    @pytest.mark.asyncio
    async def test_raises_not_found_when_thread_missing(self, use_case):
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                thread_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
            )

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_replies(self, use_case, thread_repo, channel_id):
        thread = _make_thread(channel_id)
        await thread_repo.create(thread)
        result = await use_case.execute(
            thread_id=str(thread.id),
            user_id=str(uuid.uuid4()),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_replies_for_thread(self, use_case, thread_repo, channel_id):
        thread = _make_thread(channel_id)
        await thread_repo.create(thread)
        reply = _make_reply(thread.id, channel_id)
        thread_repo.add_reply(reply)

        result = await use_case.execute(
            thread_id=str(thread.id),
            user_id=str(uuid.uuid4()),
        )
        assert len(result) == 1
        assert result[0].id == reply.id

    @pytest.mark.asyncio
    async def test_before_id_pivot_not_found_returns_all_replies(
        self, use_case, thread_repo, channel_id
    ):
        thread = _make_thread(channel_id)
        await thread_repo.create(thread)
        reply = _make_reply(thread.id, channel_id)
        thread_repo.add_reply(reply)

        # before_id points to a message not in msg_repo — pivot stays None
        result = await use_case.execute(
            thread_id=str(thread.id),
            user_id=str(uuid.uuid4()),
            before_id=str(uuid.uuid4()),
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_before_id_filters_newer_replies(
        self, use_case, thread_repo, msg_repo, channel_id
    ):
        thread = _make_thread(channel_id)
        await thread_repo.create(thread)

        r1 = _make_reply(thread.id, channel_id, offset_seconds=0)
        r2 = _make_reply(thread.id, channel_id, offset_seconds=10)
        r3 = _make_reply(thread.id, channel_id, offset_seconds=20)

        thread_repo.add_reply(r1)
        thread_repo.add_reply(r2)
        thread_repo.add_reply(r3)
        # Also store in msg_repo so the pivot lookup works
        await msg_repo.create(r1)
        await msg_repo.create(r2)
        await msg_repo.create(r3)

        result = await use_case.execute(
            thread_id=str(thread.id),
            user_id=str(uuid.uuid4()),
            before_id=str(r3.id),
        )
        result_ids = {m.id for m in result}
        assert r3.id not in result_ids
        assert r1.id in result_ids or r2.id in result_ids

    @pytest.mark.asyncio
    async def test_respects_limit(self, use_case, thread_repo, channel_id):
        thread = _make_thread(channel_id)
        await thread_repo.create(thread)
        for i in range(5):
            thread_repo.add_reply(_make_reply(thread.id, channel_id, offset_seconds=i))

        result = await use_case.execute(
            thread_id=str(thread.id),
            user_id=str(uuid.uuid4()),
            limit=3,
        )
        assert len(result) == 3
