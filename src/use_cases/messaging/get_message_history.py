"""GetMessageHistoryUseCase — cursor-paginated message history for a channel."""

from datetime import datetime
from uuid import UUID

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError
from src.domain.repositories.membership_repository import MembershipRepository
from src.domain.repositories.message_repository import MessageRepository


class GetMessageHistoryUseCase:
    def __init__(
        self,
        message_repo: MessageRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._message_repo = message_repo
        self._membership_repo = membership_repo

    async def execute(
        self,
        channel_id: str,
        user_id: str,
        limit: int = 50,
        before_id: str | None = None,
    ) -> list[Message]:
        channel_uuid = UUID(channel_id)
        user_uuid = UUID(user_id)

        is_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
        if not is_member:
            raise AuthorizationError("User is not a member of this channel.")

        before_ts: datetime | None = None
        if before_id:
            pivot = await self._message_repo.get_by_id(UUID(before_id))
            if pivot:
                before_ts = pivot.created_at

        return await self._message_repo.get_by_channel(
            channel_id=channel_uuid,
            limit=limit,
            before=before_ts,
        )
