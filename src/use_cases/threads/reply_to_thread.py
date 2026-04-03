"""ReplyToThreadUseCase — create a message as a reply within a thread."""

import uuid
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.domain.repositories.membership_repository import MembershipRepository
from src.domain.repositories.message_repository import MessageRepository
from src.domain.repositories.thread_repository import ThreadRepository

MAX_CONTENT_LENGTH = 4000


class ReplyToThreadUseCase:
    def __init__(
        self,
        thread_repo: ThreadRepository,
        message_repo: MessageRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._thread_repo = thread_repo
        self._message_repo = message_repo
        self._membership_repo = membership_repo

    async def execute(self, thread_id: str, user_id: str, content: str) -> Message:
        content = content.strip()
        if not content:
            raise ValidationError("Reply content must not be empty.")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValidationError(f"Content exceeds {MAX_CONTENT_LENGTH} characters.")

        thread_uuid = UUID(thread_id)
        thread = await self._thread_repo.get_by_id(thread_uuid)
        if thread is None:
            raise EntityNotFoundError(f"Thread '{thread_id}' not found.")

        user_uuid = UUID(user_id)
        is_member = await self._membership_repo.is_member(user_uuid, thread.channel_id)
        if not is_member:
            raise AuthorizationError("User is not a member of this channel.")

        message = Message(
            id=uuid.uuid4(),
            content=content,
            channel_id=thread.channel_id,
            user_id=user_uuid,
            thread_id=thread_uuid,
        )
        return await self._message_repo.create(message)
