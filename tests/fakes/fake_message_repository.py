"""In-memory MessageRepository for unit/integration tests — no database dependency."""

from datetime import datetime
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository


class FakeMessageRepository(MessageRepository):
    """Stores messages in a list; supports cursor-based pagination."""

    def __init__(self) -> None:
        self._store: dict[UUID, Message] = {}

    async def create(self, message: Message) -> Message:
        self._store[message.id] = message
        return message

    async def get_by_id(self, message_id: UUID) -> Message | None:
        return self._store.get(message_id)

    async def get_by_channel(
        self,
        channel_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        messages = [m for m in self._store.values() if m.channel_id == channel_id]
        if before is not None:
            messages = [m for m in messages if m.created_at < before]
        messages.sort(key=lambda m: m.created_at, reverse=True)
        return messages[:limit]

    async def count_by_channel(self, channel_id: UUID) -> int:
        """Return total message count for a channel (in-memory filter)."""
        return len([m for m in self._store.values() if m.channel_id == channel_id])

    async def search_by_content(
        self,
        query: str,
        channel_ids: list[UUID],
        limit: int = 20,
    ) -> list[Message]:
        """Case-insensitive substring search across specified channels."""
        channel_id_set = set(channel_ids)
        query_lower = query.lower()
        results = [
            m
            for m in self._store.values()
            if m.channel_id in channel_id_set and query_lower in m.content.lower()
        ]
        results.sort(key=lambda m: m.created_at, reverse=True)
        return results[:limit]

    async def update(self, message: Message) -> Message:
        if message.id not in self._store:
            raise EntityNotFoundError(f"Message '{message.id}' not found.")
        self._store[message.id] = message
        return message

    async def delete(self, message_id: UUID) -> None:
        if message_id not in self._store:
            raise EntityNotFoundError(f"Message '{message_id}' not found.")
        del self._store[message_id]
