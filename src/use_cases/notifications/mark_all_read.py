"""MarkAllReadUseCase — mark all notifications for a user as read."""

from uuid import UUID

from src.domain.repositories.notification_repository import NotificationRepository


class MarkAllReadUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._repo = notification_repo

    async def execute(self, user_id: str) -> None:
        await self._repo.mark_all_read(UUID(user_id))
