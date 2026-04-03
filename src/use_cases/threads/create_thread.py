"""CreateThreadUseCase — create a thread rooted at a parent message."""

import uuid
from uuid import UUID

from src.domain.entities.thread import Thread
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository
from src.domain.repositories.thread_repository import ThreadRepository


class CreateThreadUseCase:
    def __init__(
        self,
        thread_repo: ThreadRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._thread_repo = thread_repo
        self._message_repo = message_repo

    async def execute(self, parent_message_id: str, user_id: str) -> Thread:
        msg_uuid = UUID(parent_message_id)
        message = await self._message_repo.get_by_id(msg_uuid)
        if message is None:
            raise EntityNotFoundError(f"Message '{parent_message_id}' not found.")

        existing = await self._thread_repo.get_by_parent_message_id(msg_uuid)
        if existing is not None:
            raise DuplicateEntityError(
                f"Thread already exists for message '{parent_message_id}'."
            )

        thread = Thread(
            id=uuid.uuid4(),
            channel_id=message.channel_id,
            parent_message_id=msg_uuid,
        )
        return await self._thread_repo.create(thread)
