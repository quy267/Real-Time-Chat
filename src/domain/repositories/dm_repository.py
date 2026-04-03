"""Abstract DirectMessageRepository — async interface for DM conversation persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.direct_conversation import DirectConversation


class DirectMessageRepository(ABC):
    @abstractmethod
    async def create_conversation(self, user_ids: list[UUID]) -> DirectConversation:
        """Create a new DM conversation and add given users as members."""

    @abstractmethod
    async def get_conversation(self, conversation_id: UUID) -> DirectConversation | None:
        """Return conversation by primary key, or None if not found."""

    @abstractmethod
    async def get_conversation_by_participants(
        self, user_id_1: UUID, user_id_2: UUID
    ) -> DirectConversation | None:
        """Return conversation between exactly these two users, or None."""

    @abstractmethod
    async def list_conversations(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[DirectConversation]:
        """Return paginated DM conversations for a user."""

    @abstractmethod
    async def add_member(self, conversation_id: UUID, user_id: UUID) -> None:
        """Add a user to an existing conversation."""

    @abstractmethod
    async def is_participant(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Return True if user_id is a member of conversation_id."""
