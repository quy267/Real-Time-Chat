"""In-memory ReactionRepository for unit/integration tests — no database dependency."""

from uuid import UUID

from src.domain.entities.reaction import Reaction
from src.domain.repositories.reaction_repository import ReactionRepository


class FakeReactionRepository(ReactionRepository):
    """Stores reactions in a list keyed by (message_id, user_id, emoji)."""

    def __init__(self) -> None:
        self._store: dict[tuple[UUID, UUID, str], Reaction] = {}

    async def add(self, reaction: Reaction) -> Reaction:
        key = (reaction.message_id, reaction.user_id, reaction.emoji)
        self._store[key] = reaction
        return reaction

    async def remove(self, message_id: UUID, user_id: UUID, emoji: str) -> None:
        self._store.pop((message_id, user_id, emoji), None)

    async def list_by_message(self, message_id: UUID) -> list[Reaction]:
        return [r for r in self._store.values() if r.message_id == message_id]

    async def get(self, message_id: UUID, user_id: UUID, emoji: str) -> Reaction | None:
        return self._store.get((message_id, user_id, emoji))
