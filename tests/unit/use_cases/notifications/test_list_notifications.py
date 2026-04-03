"""Unit tests for ListNotificationsUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.notification import Notification
from src.use_cases.notifications.list_notifications import ListNotificationsUseCase
from tests.fakes.fake_notification_repository import FakeNotificationRepository


def _make_notification(user_id: uuid.UUID, read: bool = False, offset_secs: int = 0) -> Notification:
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type="mention",
        title="Test",
        content="test notification",
        reference_id=None,
        read=read,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=offset_secs),
    )


@pytest.fixture
def repo():
    return FakeNotificationRepository()


@pytest.fixture
def uc(repo):
    return ListNotificationsUseCase(repo)


async def test_list_notifications_returns_user_notifications(uc, repo):
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()

    n1 = await repo.create(_make_notification(user_id))
    await repo.create(_make_notification(other_id))

    results = await uc.execute(user_id=str(user_id))

    assert len(results) == 1
    assert results[0].id == n1.id


async def test_list_notifications_pagination(uc, repo):
    user_id = uuid.uuid4()

    for i in range(5):
        await repo.create(_make_notification(user_id, offset_secs=i))

    page1 = await uc.execute(user_id=str(user_id), limit=3, offset=0)
    page2 = await uc.execute(user_id=str(user_id), limit=3, offset=3)

    assert len(page1) == 3
    assert len(page2) == 2


async def test_list_notifications_unread_only_filter(uc, repo):
    user_id = uuid.uuid4()

    await repo.create(_make_notification(user_id, read=True))
    await repo.create(_make_notification(user_id, read=False))
    await repo.create(_make_notification(user_id, read=False))

    results = await uc.execute(user_id=str(user_id), unread_only=True)

    assert len(results) == 2
    assert all(not n.read for n in results)


async def test_list_notifications_empty_for_new_user(uc):
    user_id = str(uuid.uuid4())

    results = await uc.execute(user_id=user_id)

    assert results == []


async def test_list_notifications_ordered_newest_first(uc, repo):
    user_id = uuid.uuid4()

    old = await repo.create(_make_notification(user_id, offset_secs=100))
    new = await repo.create(_make_notification(user_id, offset_secs=0))

    results = await uc.execute(user_id=str(user_id))

    assert results[0].id == new.id
    assert results[1].id == old.id
