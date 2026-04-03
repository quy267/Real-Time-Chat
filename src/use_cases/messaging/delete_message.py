"""DeleteMessageUseCase — verify author ownership and remove a message."""

from uuid import UUID

from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository


class DeleteMessageUseCase:
    def __init__(self, message_repo: MessageRepository) -> None:
        self._message_repo = message_repo

    async def execute(self, message_id: str, user_id: str) -> None:
        message_uuid = UUID(message_id)
        user_uuid = UUID(user_id)

        message = await self._message_repo.get_by_id(message_uuid)
        if not message:
            raise EntityNotFoundError(f"Message '{message_id}' not found.")

        if message.user_id != user_uuid:
            raise AuthorizationError("Only the author can delete this message.")

        await self._message_repo.delete(message_uuid)
