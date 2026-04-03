"""MarkNotificationReadUseCase — mark a single notification as read, verifying ownership."""

from uuid import UUID

from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.notification_repository import NotificationRepository


class MarkNotificationReadUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._repo = notification_repo

    async def execute(self, notification_id: str, user_id: str) -> None:
        notif_uuid = UUID(notification_id)
        user_uuid = UUID(user_id)

        notification = await self._repo.get_by_id(notif_uuid)
        if notification is None:
            raise EntityNotFoundError(f"Notification {notification_id} not found")
        if notification.user_id != user_uuid:
            raise AuthorizationError("Cannot mark another user's notification as read")

        await self._repo.mark_read(notif_uuid, user_uuid)
