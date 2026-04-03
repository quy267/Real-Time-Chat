"""In-memory DirectMessageRepository for unit/integration tests — no database dependency."""

import uuid
from uuid import UUID

from src.domain.entities.direct_conversation import DirectConversation, DirectConversationMember
from src.domain.repositories.dm_repository import DirectMessageRepository


class FakeDmRepository(DirectMessageRepository):
    """Stores DM conversations and members in memory."""

    def __init__(self) -> None:
        self._conversations: dict[UUID, DirectConversation] = {}
        self._members: list[DirectConversationMember] = []

    async def create_conversation(self, user_ids: list[UUID]) -> DirectConversation:
        conversation = DirectConversation(id=uuid.uuid4())
        self._conversations[conversation.id] = conversation
        for uid in user_ids:
            self._members.append(
                DirectConversationMember(conversation_id=conversation.id, user_id=uid)
            )
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> DirectConversation | None:
        return self._conversations.get(conversation_id)

    async def get_conversation_by_participants(
        self, user_id_1: UUID, user_id_2: UUID
    ) -> DirectConversation | None:
        for conv in self._conversations.values():
            members = {m.user_id for m in self._members if m.conversation_id == conv.id}
            if members == {user_id_1, user_id_2}:
                return conv
        return None

    async def list_conversations(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[DirectConversation]:
        conv_ids = {m.conversation_id for m in self._members if m.user_id == user_id}
        result = [c for c in self._conversations.values() if c.id in conv_ids]
        result.sort(key=lambda c: c.created_at)
        return result[offset : offset + limit]

    async def add_member(self, conversation_id: UUID, user_id: UUID) -> None:
        self._members.append(
            DirectConversationMember(conversation_id=conversation_id, user_id=user_id)
        )

    async def is_participant(self, conversation_id: UUID, user_id: UUID) -> bool:
        return any(
            m.conversation_id == conversation_id and m.user_id == user_id
            for m in self._members
        )
