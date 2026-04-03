"""GetThreadRepliesUseCase — fetch paginated replies for a thread."""

from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository
from src.domain.repositories.thread_repository import ThreadRepository


class GetThreadRepliesUseCase:
    def __init__(
        self,
        thread_repo: ThreadRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._thread_repo = thread_repo
        self._message_repo = message_repo

    async def execute(
        self,
        thread_id: str,
        user_id: str,
        limit: int = 50,
        before_id: str | None = None,
    ) -> list[Message]:
        thread_uuid = UUID(thread_id)
        thread = await self._thread_repo.get_by_id(thread_uuid)
        if thread is None:
            raise EntityNotFoundError(f"Thread '{thread_id}' not found.")

        before_dt = None
        if before_id:
            pivot = await self._message_repo.get_by_id(UUID(before_id))
            if pivot:
                before_dt = pivot.created_at

        return await self._thread_repo.get_replies(
            thread_id=thread_uuid,
            limit=limit,
            before=before_dt,
        )
