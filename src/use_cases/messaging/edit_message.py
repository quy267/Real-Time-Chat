"""EditMessageUseCase — update message content, verify author ownership."""

from datetime import datetime, timezone
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.domain.repositories.message_repository import MessageRepository

MAX_CONTENT_LENGTH = 4000


class EditMessageUseCase:
    def __init__(self, message_repo: MessageRepository) -> None:
        self._message_repo = message_repo

    async def execute(
        self,
        message_id: str,
        user_id: str,
        new_content: str,
    ) -> Message:
        new_content = new_content.strip()
        if not new_content:
            raise ValidationError("Message content must not be empty.")
        if len(new_content) > MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Message content exceeds {MAX_CONTENT_LENGTH} characters."
            )

        message_uuid = UUID(message_id)
        user_uuid = UUID(user_id)

        message = await self._message_repo.get_by_id(message_uuid)
        if not message:
            raise EntityNotFoundError(f"Message '{message_id}' not found.")

        if message.user_id != user_uuid:
            raise AuthorizationError("Only the author can edit this message.")

        message.content = new_content
        message.updated_at = datetime.now(timezone.utc)
        return await self._message_repo.update(message)
