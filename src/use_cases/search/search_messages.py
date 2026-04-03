"""SearchMessagesUseCase — case-insensitive substring search across channel messages."""

from uuid import UUID

from src.domain.entities.message import Message
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository
from src.domain.repositories.message_repository import MessageRepository


class SearchMessagesUseCase:
    def __init__(
        self,
        message_repo: MessageRepository,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._message_repo = message_repo
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(
        self,
        query: str,
        user_id: str,
        channel_id: str | None = None,
        limit: int = 20,
    ) -> list[Message]:
        """Search messages by substring; respects channel membership.

        If channel_id is provided, searches only that channel (if user is member).
        Otherwise searches all channels the user is a member of.
        Returns up to `limit` results sorted by recency (newest first).
        """
        query = query.strip()
        if not query:
            return []

        user_uuid = UUID(user_id)

        if channel_id is not None:
            channel_uuid = UUID(channel_id)
            is_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
            if not is_member:
                return []
            channel_ids = [channel_uuid]
        else:
            # list_by_user returns channels the user is a member of
            channels = await self._channel_repo.list_by_user(user_uuid)
            channel_ids = [c.id for c in channels]

        return await self._message_repo.search_by_content(query, channel_ids, limit=limit)
