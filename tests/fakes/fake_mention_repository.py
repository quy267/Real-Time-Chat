"""In-memory MentionRepository for unit/integration tests — no database dependency."""

from uuid import UUID

from src.domain.entities.mention import Mention
from src.domain.repositories.mention_repository import MentionRepository


class FakeMentionRepository(MentionRepository):
    """Stores mentions in a list; keyed by mention.id."""

    def __init__(self) -> None:
        self._store: dict[UUID, Mention] = {}

    async def create(self, mention: Mention) -> Mention:
        self._store[mention.id] = mention
        return mention

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Mention]:
        result = [m for m in self._store.values() if m.mentioned_user_id == user_id]
        result.sort(key=lambda m: m.created_at)
        return result[offset : offset + limit]
