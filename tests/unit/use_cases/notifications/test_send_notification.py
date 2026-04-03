"""Unit tests for SendNotificationUseCase."""

import uuid

import pytest

from src.use_cases.notifications.send_notification import SendNotificationUseCase
from tests.fakes.fake_notification_repository import FakeNotificationRepository


@pytest.fixture
def repo():
    return FakeNotificationRepository()


@pytest.fixture
def uc(repo):
    return SendNotificationUseCase(repo)


async def test_send_notification_creates_record(uc, repo):
    user_id = str(uuid.uuid4())
    result = await uc.execute(
        user_id=user_id,
        notification_type="mention",
        title="You were mentioned",
        content="alice mentioned you in #general",
        reference_id=str(uuid.uuid4()),
    )

    assert result.id is not None
    stored = await repo.get_by_id(result.id)
    assert stored is not None
    assert stored.user_id == uuid.UUID(user_id)


async def test_send_notification_correct_type_and_content(uc):
    user_id = str(uuid.uuid4())
    ref_id = str(uuid.uuid4())

    result = await uc.execute(
        user_id=user_id,
        notification_type="dm",
        title="New DM",
        content="bob sent you a message",
        reference_id=ref_id,
    )

    assert result.type == "dm"
    assert result.title == "New DM"
    assert result.content == "bob sent you a message"
    assert result.reference_id == ref_id


async def test_send_notification_defaults_to_unread(uc):
    user_id = str(uuid.uuid4())

    result = await uc.execute(
        user_id=user_id,
        notification_type="mention",
        title="Mention",
        content="you were mentioned",
    )

    assert result.read is False


async def test_send_notification_without_reference_id(uc):
    user_id = str(uuid.uuid4())

    result = await uc.execute(
        user_id=user_id,
        notification_type="channel_invite",
        title="Channel Invite",
        content="you were invited to #random",
        reference_id=None,
    )

    assert result.reference_id is None
    assert result.id is not None


async def test_send_notification_increments_unread_count(uc, repo):
    user_id = str(uuid.uuid4())

    await uc.execute(
        user_id=user_id,
        notification_type="mention",
        title="Mention 1",
        content="first mention",
    )
    await uc.execute(
        user_id=user_id,
        notification_type="dm",
        title="DM 1",
        content="first dm",
    )

    count = await repo.count_unread(uuid.UUID(user_id))
    assert count == 2
