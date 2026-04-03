"""In-memory NotificationRepository for unit/integration tests — no database dependency."""

from uuid import UUID

from src.domain.entities.notification import Notification
from src.domain.repositories.notification_repository import NotificationRepository


class FakeNotificationRepository(NotificationRepository):
    """Stores notifications in a dict keyed by notification.id."""

    def __init__(self) -> None:
        self._store: dict[UUID, Notification] = {}

    async def create(self, notification: Notification) -> Notification:
        self._store[notification.id] = notification
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        return self._store.get(notification_id)

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        results = [n for n in self._store.values() if n.user_id == user_id]
        if unread_only:
            results = [n for n in results if not n.read]
        results.sort(key=lambda n: n.created_at, reverse=True)
        return results[offset : offset + limit]

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        notification = self._store.get(notification_id)
        if notification and notification.user_id == user_id:
            notification.read = True

    async def mark_all_read(self, user_id: UUID) -> None:
        for notification in self._store.values():
            if notification.user_id == user_id:
                notification.read = True

    async def count_unread(self, user_id: UUID) -> int:
        return sum(
            1 for n in self._store.values() if n.user_id == user_id and not n.read
        )
