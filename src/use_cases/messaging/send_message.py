"""SendMessageUseCase — validate, persist, and return a new chat message."""

import uuid
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, ValidationError
from src.domain.repositories.membership_repository import MembershipRepository
from src.domain.repositories.message_repository import MessageRepository

MAX_CONTENT_LENGTH = 4000


class SendMessageUseCase:
    def __init__(
        self,
        message_repo: MessageRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._message_repo = message_repo
        self._membership_repo = membership_repo

    async def execute(
        self,
        content: str,
        channel_id: str,
        user_id: str,
        thread_id: str | None = None,
        file_url: str | None = None,
    ) -> Message:
        content = content.strip()
        if not content:
            raise ValidationError("Message content must not be empty.")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Message content exceeds {MAX_CONTENT_LENGTH} characters."
            )

        channel_uuid = UUID(channel_id)
        user_uuid = UUID(user_id)
        is_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
        if not is_member:
            raise AuthorizationError("User is not a member of this channel.")

        message = Message(
            id=uuid.uuid4(),
            content=content,
            channel_id=channel_uuid,
            user_id=user_uuid,
            thread_id=UUID(thread_id) if thread_id else None,
            file_url=file_url,
        )
        return await self._message_repo.create(message)
