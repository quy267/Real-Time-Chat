"""Abstract ThreadRepository — async interface for thread persistence."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.entities.thread import Thread


class ThreadRepository(ABC):
    @abstractmethod
    async def create(self, thread: Thread) -> Thread:
        """Persist a new thread and return it."""

    @abstractmethod
    async def get_by_id(self, thread_id: UUID) -> Thread | None:
        """Return thread by primary key, or None if not found."""

    @abstractmethod
    async def get_by_parent_message_id(self, parent_message_id: UUID) -> Thread | None:
        """Return the thread rooted at the given message, or None."""

    @abstractmethod
    async def get_replies(
        self,
        thread_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        """Return paginated reply messages for a thread.

        Cursor-based: returns `limit` messages created before `before`.
        """
