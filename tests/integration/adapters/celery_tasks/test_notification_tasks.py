"""Integration tests for notification Celery tasks — called directly (no broker required)."""

import uuid
from unittest.mock import patch

import pytest

from tests.fakes.fake_notification_repository import FakeNotificationRepository


@pytest.fixture
def fake_repo():
    return FakeNotificationRepository()


def _patch_repo(fake_repo):
    """Patch the _get_notification_repo function to return the fake repo."""
    return patch(
        "src.adapters.celery_tasks.notification_tasks._get_notification_repo",
        return_value=fake_repo,
    )


def test_send_mention_notification_creates_notification(fake_repo):
    """Calling the task function directly creates a mention notification."""
    from src.adapters.celery_tasks.notification_tasks import send_mention_notification

    user_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    with _patch_repo(fake_repo):
        result = send_mention_notification(
            mentioned_user_id=user_id,
            message_id=message_id,
            mentioner_username="alice",
            channel_name="general",
        )

    assert result["status"] == "created"
    assert "notification_id" in result

    notif_id = uuid.UUID(result["notification_id"])
    import asyncio

    stored = asyncio.run(fake_repo.get_by_id(notif_id))
    assert stored is not None
    assert stored.type == "mention"
    assert stored.user_id == uuid.UUID(user_id)
    assert stored.reference_id == message_id
    assert "@alice" in stored.content
    assert "general" in stored.content


def test_send_dm_notification_creates_notification(fake_repo):
    """Calling the task function directly creates a DM notification."""
    from src.adapters.celery_tasks.notification_tasks import send_dm_notification

    recipient_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    with _patch_repo(fake_repo):
        result = send_dm_notification(
            recipient_id=recipient_id,
            sender_username="bob",
            conversation_id=conversation_id,
        )

    assert result["status"] == "created"

    notif_id = uuid.UUID(result["notification_id"])
    import asyncio

    stored = asyncio.run(fake_repo.get_by_id(notif_id))
    assert stored is not None
    assert stored.type == "dm"
    assert stored.user_id == uuid.UUID(recipient_id)
    assert stored.reference_id == conversation_id
    assert "@bob" in stored.content


def test_mention_notification_is_unread_by_default(fake_repo):
    import asyncio

    from src.adapters.celery_tasks.notification_tasks import send_mention_notification

    user_id = str(uuid.uuid4())

    with _patch_repo(fake_repo):
        result = send_mention_notification(
            mentioned_user_id=user_id,
            message_id=str(uuid.uuid4()),
            mentioner_username="carol",
            channel_name="dev",
        )

    stored = asyncio.run(fake_repo.get_by_id(uuid.UUID(result["notification_id"])))
    assert stored.read is False


def test_dm_notification_is_unread_by_default(fake_repo):
    import asyncio

    from src.adapters.celery_tasks.notification_tasks import send_dm_notification

    recipient_id = str(uuid.uuid4())

    with _patch_repo(fake_repo):
        result = send_dm_notification(
            recipient_id=recipient_id,
            sender_username="dave",
            conversation_id=str(uuid.uuid4()),
        )

    stored = asyncio.run(fake_repo.get_by_id(uuid.UUID(result["notification_id"])))
    assert stored.read is False
