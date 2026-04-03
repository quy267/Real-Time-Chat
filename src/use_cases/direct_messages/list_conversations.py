"""ListConversationsUseCase — list DM conversations for the current user."""

from uuid import UUID

from src.domain.entities.direct_conversation import DirectConversation
from src.domain.repositories.dm_repository import DirectMessageRepository


class ListConversationsUseCase:
    def __init__(self, dm_repo: DirectMessageRepository) -> None:
        self._dm_repo = dm_repo

    async def execute(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[DirectConversation]:
        return await self._dm_repo.list_conversations(
            user_id=UUID(user_id),
            limit=limit,
            offset=offset,
        )
