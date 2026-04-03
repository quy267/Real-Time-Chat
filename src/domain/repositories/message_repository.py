"""Abstract MessageRepository — async interface for message persistence."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities.message import Message


class MessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message:
        """Persist a new message and return it."""

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Message | None:
        """Return message by primary key, or None if not found."""

    @abstractmethod
    async def get_by_channel(
        self,
        channel_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        """Return paginated messages for a channel.

        Cursor-based: returns `limit` messages created before `before`
        timestamp (newest-first). Pass before=None for the latest page.
        """

    @abstractmethod
    async def count_by_channel(self, channel_id: UUID) -> int:
        """Return total number of messages in a channel (SELECT COUNT(*))."""

    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        channel_ids: list[UUID],
        limit: int = 20,
    ) -> list[Message]:
        """Return messages whose content matches query (case-insensitive) across channels.

        Results sorted newest-first. Used by SearchMessagesUseCase to avoid N+1.
        """

    @abstractmethod
    async def update(self, message: Message) -> Message:
        """Persist changes to an existing message and return updated entity."""

    @abstractmethod
    async def delete(self, message_id: UUID) -> None:
        """Remove a message by primary key."""
