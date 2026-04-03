"""Celery tasks for delivering notifications to users asynchronously."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from src.domain.entities.notification import Notification
from src.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from sync Celery context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _get_notification_repo():
    """Get notification repository — SQLAlchemy implementation only."""
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_notification_repository import (
        SQLAlchemyNotificationRepository,
    )

    return SQLAlchemyNotificationRepository(async_session_factory())


@celery_app.task(name="notification_tasks.send_mention_notification", bind=True, max_retries=3)
def send_mention_notification(
    self,
    mentioned_user_id: str,
    message_id: str,
    mentioner_username: str,
    channel_name: str,
) -> dict:
    """Queue a mention notification for a user."""
    logger.info(
        "Sending mention notification to user=%s from=%s in #%s",
        mentioned_user_id,
        mentioner_username,
        channel_name,
    )

    notification = Notification(
        id=uuid.uuid4(),
        user_id=uuid.UUID(mentioned_user_id),
        type="mention",
        title=f"@{mentioner_username} mentioned you",
        content=f"You were mentioned by @{mentioner_username} in #{channel_name}",
        reference_id=message_id,
        read=False,
        created_at=datetime.now(timezone.utc),
    )

    try:
        repo = _get_notification_repo()
        _run_async(repo.create(notification))
        logger.info("Mention notification created: %s", notification.id)
        return {"notification_id": str(notification.id), "status": "created"}
    except Exception as exc:
        logger.error("Failed to create mention notification: %s", exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(name="notification_tasks.send_dm_notification", bind=True, max_retries=3)
def send_dm_notification(
    self,
    recipient_id: str,
    sender_username: str,
    conversation_id: str,
) -> dict:
    """Queue a DM notification for a user."""
    logger.info(
        "Sending DM notification to user=%s from=%s conv=%s",
        recipient_id,
        sender_username,
        conversation_id,
    )

    notification = Notification(
        id=uuid.uuid4(),
        user_id=uuid.UUID(recipient_id),
        type="dm",
        title=f"New message from @{sender_username}",
        content=f"@{sender_username} sent you a direct message",
        reference_id=conversation_id,
        read=False,
        created_at=datetime.now(timezone.utc),
    )

    try:
        repo = _get_notification_repo()
        _run_async(repo.create(notification))
        logger.info("DM notification created: %s", notification.id)
        return {"notification_id": str(notification.id), "status": "created"}
    except Exception as exc:
        logger.error("Failed to create DM notification: %s", exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
