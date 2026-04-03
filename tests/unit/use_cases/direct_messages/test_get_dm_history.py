"""Unit tests for GetDmHistoryUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.use_cases.direct_messages.get_dm_history import GetDmHistoryUseCase
from src.use_cases.direct_messages.send_direct_message import dm_channel_id
from tests.fakes.fake_dm_repository import FakeDmRepository
from tests.fakes.fake_message_repository import FakeMessageRepository


def _make_message(channel_id: uuid.UUID, offset_seconds: int = 0) -> Message:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return Message(
        id=uuid.uuid4(),
        content="test message",
        channel_id=channel_id,
        user_id=uuid.uuid4(),
        created_at=base + timedelta(seconds=offset_seconds),
        updated_at=base,
    )


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def other_user_id():
    return uuid.uuid4()


@pytest.fixture
def dm_repo():
    return FakeDmRepository()


@pytest.fixture
def msg_repo():
    return FakeMessageRepository()


@pytest.fixture
def use_case(dm_repo, msg_repo):
    return GetDmHistoryUseCase(dm_repo=dm_repo, message_repo=msg_repo)


class TestGetDmHistoryUseCase:
    @pytest.mark.asyncio
    async def test_raises_not_found_when_conversation_missing(self, use_case, user_id):
        missing_id = str(uuid.uuid4())
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                conversation_id=missing_id,
                user_id=str(user_id),
            )

    @pytest.mark.asyncio
    async def test_raises_authorization_error_when_not_participant(
        self, use_case, dm_repo, user_id, other_user_id
    ):
        conv = await dm_repo.create_conversation([other_user_id, uuid.uuid4()])
        with pytest.raises(AuthorizationError):
            await use_case.execute(
                conversation_id=str(conv.id),
                user_id=str(user_id),
            )

    @pytest.mark.asyncio
    async def test_returns_messages_for_participant(
        self, use_case, dm_repo, msg_repo, user_id, other_user_id
    ):
        conv = await dm_repo.create_conversation([user_id, other_user_id])
        pseudo_channel = dm_channel_id(conv.id)
        msg = _make_message(pseudo_channel)
        await msg_repo.create(msg)

        result = await use_case.execute(
            conversation_id=str(conv.id),
            user_id=str(user_id),
        )
        assert len(result) == 1
        assert result[0].id == msg.id

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_messages(
        self, use_case, dm_repo, user_id, other_user_id
    ):
        conv = await dm_repo.create_conversation([user_id, other_user_id])
        result = await use_case.execute(
            conversation_id=str(conv.id),
            user_id=str(user_id),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_before_id_filters_older_messages(
        self, use_case, dm_repo, msg_repo, user_id, other_user_id
    ):
        conv = await dm_repo.create_conversation([user_id, other_user_id])
        pseudo_channel = dm_channel_id(conv.id)
        m1 = _make_message(pseudo_channel, offset_seconds=0)
        m2 = _make_message(pseudo_channel, offset_seconds=10)
        m3 = _make_message(pseudo_channel, offset_seconds=20)
        await msg_repo.create(m1)
        await msg_repo.create(m2)
        await msg_repo.create(m3)

        # before_id=m3 → only m1 and m2 should appear (created before m3)
        result = await use_case.execute(
            conversation_id=str(conv.id),
            user_id=str(user_id),
            before_id=str(m3.id),
        )
        result_ids = {m.id for m in result}
        assert m3.id not in result_ids
        assert m1.id in result_ids or m2.id in result_ids

    @pytest.mark.asyncio
    async def test_before_id_pivot_not_found_returns_all(
        self, use_case, dm_repo, msg_repo, user_id, other_user_id
    ):
        conv = await dm_repo.create_conversation([user_id, other_user_id])
        pseudo_channel = dm_channel_id(conv.id)
        msg = _make_message(pseudo_channel)
        await msg_repo.create(msg)

        # Non-existent pivot → before_dt stays None → all messages returned
        result = await use_case.execute(
            conversation_id=str(conv.id),
            user_id=str(user_id),
            before_id=str(uuid.uuid4()),
        )
        assert len(result) == 1
