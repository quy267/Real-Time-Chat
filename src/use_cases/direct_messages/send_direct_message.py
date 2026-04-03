"""SendDirectMessageUseCase — send a message within a DM conversation."""

import uuid
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.domain.repositories.dm_repository import DirectMessageRepository
from src.domain.repositories.message_repository import MessageRepository

MAX_CONTENT_LENGTH = 4000

# Sentinel UUID: DM messages store conversation_id encoded as channel_id.
# The prefix "dm:" is conveyed by using a stable namespace UUID XOR'd with
# conversation_id so callers can distinguish DM vs channel messages.
# At the use-case layer we simply pass conversation_id as channel_id;
# the MessageRepository is reused without schema changes.
_DM_NAMESPACE = UUID("00000000-0000-0000-0000-000000000000")


def dm_channel_id(conversation_id: UUID) -> UUID:
    """Derive a deterministic pseudo channel_id for a DM conversation."""
    return uuid.uuid5(_DM_NAMESPACE, f"dm:{conversation_id}")


class SendDirectMessageUseCase:
    def __init__(
        self,
        dm_repo: DirectMessageRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._dm_repo = dm_repo
        self._message_repo = message_repo

    async def execute(
        self, conversation_id: str, user_id: str, content: str
    ) -> Message:
        content = content.strip()
        if not content:
            raise ValidationError("Message content must not be empty.")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValidationError(f"Content exceeds {MAX_CONTENT_LENGTH} characters.")

        conv_uuid = UUID(conversation_id)
        user_uuid = UUID(user_id)

        conversation = await self._dm_repo.get_conversation(conv_uuid)
        if conversation is None:
            raise EntityNotFoundError(f"Conversation '{conversation_id}' not found.")

        is_participant = await self._dm_repo.is_participant(conv_uuid, user_uuid)
        if not is_participant:
            raise AuthorizationError("User is not a participant in this conversation.")

        message = Message(
            id=uuid.uuid4(),
            content=content,
            # Store conversation_id as channel_id via deterministic mapping
            channel_id=dm_channel_id(conv_uuid),
            user_id=user_uuid,
        )
        return await self._message_repo.create(message)
