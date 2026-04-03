"""In-memory ThreadRepository for unit/integration tests — no database dependency."""

from datetime import datetime
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.entities.thread import Thread
from src.domain.repositories.thread_repository import ThreadRepository


class FakeThreadRepository(ThreadRepository):
    """Stores threads and replies in memory."""

    def __init__(self) -> None:
        self._threads: dict[UUID, Thread] = {}
        self._replies: dict[UUID, Message] = {}

    async def create(self, thread: Thread) -> Thread:
        self._threads[thread.id] = thread
        return thread

    async def get_by_id(self, thread_id: UUID) -> Thread | None:
        return self._threads.get(thread_id)

    async def get_by_parent_message_id(self, parent_message_id: UUID) -> Thread | None:
        for thread in self._threads.values():
            if thread.parent_message_id == parent_message_id:
                return thread
        return None

    async def get_replies(
        self,
        thread_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        replies = [m for m in self._replies.values() if m.thread_id == thread_id]
        if before is not None:
            replies = [m for m in replies if m.created_at < before]
        replies.sort(key=lambda m: m.created_at, reverse=True)
        return replies[:limit]

    def add_reply(self, message: Message) -> None:
        """Helper: store a reply message for get_replies queries."""
        self._replies[message.id] = message
