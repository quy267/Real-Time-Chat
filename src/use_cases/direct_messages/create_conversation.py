"""CreateConversationUseCase — create or return existing DM conversation between two users."""

from uuid import UUID

from src.domain.entities.direct_conversation import DirectConversation
from src.domain.exceptions import ValidationError
from src.domain.repositories.dm_repository import DirectMessageRepository


class CreateConversationUseCase:
    def __init__(self, dm_repo: DirectMessageRepository) -> None:
        self._dm_repo = dm_repo

    async def execute(self, creator_id: str, other_user_id: str) -> DirectConversation:
        creator_uuid = UUID(creator_id)
        other_uuid = UUID(other_user_id)

        if creator_uuid == other_uuid:
            raise ValidationError("Cannot create a DM conversation with yourself.")

        existing = await self._dm_repo.get_conversation_by_participants(
            creator_uuid, other_uuid
        )
        if existing is not None:
            return existing

        return await self._dm_repo.create_conversation([creator_uuid, other_uuid])
