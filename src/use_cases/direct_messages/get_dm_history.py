"""GetDmHistoryUseCase — paginated message history for a DM conversation."""

from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.dm_repository import DirectMessageRepository
from src.domain.repositories.message_repository import MessageRepository
from src.use_cases.direct_messages.send_direct_message import dm_channel_id


class GetDmHistoryUseCase:
    def __init__(
        self,
        dm_repo: DirectMessageRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._dm_repo = dm_repo
        self._message_repo = message_repo

    async def execute(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        before_id: str | None = None,
    ) -> list[Message]:
        conv_uuid = UUID(conversation_id)
        user_uuid = UUID(user_id)

        conversation = await self._dm_repo.get_conversation(conv_uuid)
        if conversation is None:
            raise EntityNotFoundError(f"Conversation '{conversation_id}' not found.")

        if not await self._dm_repo.is_participant(conv_uuid, user_uuid):
            raise AuthorizationError("User is not a participant in this conversation.")

        before_dt = None
        if before_id:
            pivot = await self._message_repo.get_by_id(UUID(before_id))
            if pivot:
                before_dt = pivot.created_at

        pseudo_channel_id = dm_channel_id(conv_uuid)
        return await self._message_repo.get_by_channel(
            channel_id=pseudo_channel_id,
            limit=limit,
            before=before_dt,
        )
