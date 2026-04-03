"""Abstract ReactionRepository — async interface for reaction persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.reaction import Reaction


class ReactionRepository(ABC):
    @abstractmethod
    async def add(self, reaction: Reaction) -> Reaction:
        """Persist a new reaction and return it."""

    @abstractmethod
    async def remove(self, message_id: UUID, user_id: UUID, emoji: str) -> None:
        """Remove a specific reaction. No-op if not found."""

    @abstractmethod
    async def list_by_message(self, message_id: UUID) -> list[Reaction]:
        """Return all reactions for a given message."""

    @abstractmethod
    async def get(self, message_id: UUID, user_id: UUID, emoji: str) -> Reaction | None:
        """Return a specific reaction or None if not found."""
