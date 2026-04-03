"""SendNotificationUseCase — creates and persists a notification for a user."""

import uuid
from datetime import datetime, timezone

from src.domain.entities.notification import Notification
from src.domain.repositories.notification_repository import NotificationRepository


class SendNotificationUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._repo = notification_repo

    async def execute(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        content: str,
        reference_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            type=notification_type,
            title=title,
            content=content,
            reference_id=reference_id,
            read=False,
            created_at=datetime.now(timezone.utc),
        )
        return await self._repo.create(notification)
