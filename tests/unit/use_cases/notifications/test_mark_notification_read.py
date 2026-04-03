"""Unit tests for MarkNotificationReadUseCase and MarkAllReadUseCase."""

import uuid

import pytest

from src.domain.entities.notification import Notification
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.use_cases.notifications.mark_all_read import MarkAllReadUseCase
from src.use_cases.notifications.mark_notification_read import MarkNotificationReadUseCase
from tests.fakes.fake_notification_repository import FakeNotificationRepository


def _make_notification(user_id: uuid.UUID) -> Notification:
    from datetime import datetime, timezone

    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type="mention",
        title="Test",
        content="test notification",
        reference_id=None,
        read=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def repo():
    return FakeNotificationRepository()


@pytest.fixture
def mark_uc(repo):
    return MarkNotificationReadUseCase(repo)


@pytest.fixture
def mark_all_uc(repo):
    return MarkAllReadUseCase(repo)


async def test_mark_read_success(mark_uc, repo):
    user_id = uuid.uuid4()
    notification = await repo.create(_make_notification(user_id))

    await mark_uc.execute(
        notification_id=str(notification.id),
        user_id=str(user_id),
    )

    updated = await repo.get_by_id(notification.id)
    assert updated.read is True


async def test_mark_read_not_found_raises(mark_uc):
    with pytest.raises(EntityNotFoundError):
        await mark_uc.execute(
            notification_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )


async def test_mark_read_wrong_owner_raises(mark_uc, repo):
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    notification = await repo.create(_make_notification(owner_id))

    with pytest.raises(AuthorizationError):
        await mark_uc.execute(
            notification_id=str(notification.id),
            user_id=str(other_id),
        )


async def test_mark_all_read_marks_only_user_notifications(mark_all_uc, repo):
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()

    n_user = await repo.create(_make_notification(user_id))
    n_other = await repo.create(_make_notification(other_id))

    await mark_all_uc.execute(user_id=str(user_id))

    assert (await repo.get_by_id(n_user.id)).read is True
    assert (await repo.get_by_id(n_other.id)).read is False


async def test_mark_all_read_unread_count_becomes_zero(mark_all_uc, repo):
    user_id = uuid.uuid4()

    for _ in range(3):
        await repo.create(_make_notification(user_id))

    await mark_all_uc.execute(user_id=str(user_id))

    count = await repo.count_unread(user_id)
    assert count == 0
