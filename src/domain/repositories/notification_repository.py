"""Abstract NotificationRepository — async interface for notification persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    async def create(self, notification: Notification) -> Notification:
        """Persist a new notification and return it."""

    @abstractmethod
    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        """Return notification by id, or None if not found."""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        """Return paginated notifications for a user, optionally filtered to unread."""

    @abstractmethod
    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        """Mark a single notification as read (user_id used for ownership check)."""

    @abstractmethod
    async def mark_all_read(self, user_id: UUID) -> None:
        """Mark all notifications for a user as read."""

    @abstractmethod
    async def count_unread(self, user_id: UUID) -> int:
        """Return the count of unread notifications for a user."""
