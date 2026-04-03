"""Abstract MentionRepository — async interface for mention persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.mention import Mention


class MentionRepository(ABC):
    @abstractmethod
    async def create(self, mention: Mention) -> Mention:
        """Persist a new mention and return it."""

    @abstractmethod
    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Mention]:
        """Return paginated mentions for a given user."""
