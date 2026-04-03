"""ListNotificationsUseCase — fetch paginated notifications for the current user."""

from uuid import UUID

from src.domain.entities.notification import Notification
from src.domain.repositories.notification_repository import NotificationRepository


class ListNotificationsUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._repo = notification_repo

    async def execute(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        return await self._repo.list_by_user(
            user_id=UUID(user_id),
            limit=limit,
            offset=offset,
            unread_only=unread_only,
        )
