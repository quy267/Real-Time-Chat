"""Unit tests for GetMessageHistoryUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.membership import MemberRole
from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError
from src.use_cases.messaging.get_message_history import GetMessageHistoryUseCase
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository


def _utcnow():
    return datetime.now(timezone.utc)


@pytest.fixture
def channel_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def repos():
    return FakeMessageRepository(), FakeMembershipRepository()


@pytest.fixture
async def member_uc(repos, channel_id, user_id):
    msg_repo, mem_repo = repos
    await mem_repo.add_member(user_id, channel_id, MemberRole.MEMBER)
    uc = GetMessageHistoryUseCase(msg_repo, mem_repo)
    return uc, msg_repo, channel_id, user_id


async def _seed_messages(repo, channel_id, count=5):
    """Seed `count` messages with ascending timestamps."""
    base = _utcnow() - timedelta(minutes=count)
    messages = []
    for i in range(count):
        msg = Message(
            id=uuid.uuid4(),
            content=f"message {i}",
            channel_id=channel_id,
            user_id=uuid.uuid4(),
            created_at=base + timedelta(minutes=i),
            updated_at=base + timedelta(minutes=i),
        )
        await repo.create(msg)
        messages.append(msg)
    return messages  # oldest first


async def test_get_history_success(member_uc):
    uc, repo, channel_id, user_id = member_uc
    await _seed_messages(repo, channel_id, count=3)

    result = await uc.execute(channel_id=str(channel_id), user_id=str(user_id))

    assert len(result) == 3
    # Newest first ordering
    assert result[0].created_at >= result[-1].created_at


async def test_get_history_respects_limit(member_uc):
    uc, repo, channel_id, user_id = member_uc
    await _seed_messages(repo, channel_id, count=10)

    result = await uc.execute(channel_id=str(channel_id), user_id=str(user_id), limit=3)

    assert len(result) == 3


async def test_get_history_with_cursor(member_uc):
    uc, repo, channel_id, user_id = member_uc
    messages = await _seed_messages(repo, channel_id, count=5)

    # Cursor = newest message → should return nothing older than the very oldest
    newest = messages[-1]
    result = await uc.execute(
        channel_id=str(channel_id),
        user_id=str(user_id),
        before_id=str(newest.id),
    )
    # All messages before newest (4 messages)
    assert len(result) == 4
    for msg in result:
        assert msg.created_at < newest.created_at


async def test_get_history_empty_channel(member_uc):
    uc, repo, channel_id, user_id = member_uc
    result = await uc.execute(channel_id=str(channel_id), user_id=str(user_id))
    assert result == []


async def test_get_history_not_a_member(repos, channel_id, user_id):
    msg_repo, mem_repo = repos
    uc = GetMessageHistoryUseCase(msg_repo, mem_repo)
    with pytest.raises(AuthorizationError):
        await uc.execute(channel_id=str(channel_id), user_id=str(user_id))


async def test_get_history_invalid_cursor_returns_all(member_uc):
    """A non-existent before_id cursor returns full history (no pivot found)."""
    uc, repo, channel_id, user_id = member_uc
    await _seed_messages(repo, channel_id, count=3)

    result = await uc.execute(
        channel_id=str(channel_id),
        user_id=str(user_id),
        before_id=str(uuid.uuid4()),  # unknown ID → no timestamp filter
    )
    assert len(result) == 3
