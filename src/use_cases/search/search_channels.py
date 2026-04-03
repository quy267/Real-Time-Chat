"""SearchChannelsUseCase — search channels by name or description."""

from uuid import UUID

from src.domain.entities.channel import Channel
from src.domain.repositories.channel_repository import ChannelRepository


class SearchChannelsUseCase:
    def __init__(self, channel_repo: ChannelRepository) -> None:
        self._channel_repo = channel_repo

    async def execute(
        self,
        query: str,
        user_id: str,
        limit: int = 20,
    ) -> list[Channel]:
        """Search public channels by name or description substring.

        Returns up to `limit` results sorted by name.
        """
        query = query.strip()
        if not query:
            return []

        user_uuid = UUID(user_id)
        query_lower = query.lower()

        # list_by_user returns channels the user is a member of
        channels = await self._channel_repo.list_by_user(user_uuid)

        results = [
            c for c in channels
            if query_lower in c.name.lower()
            or (c.description and query_lower in c.description.lower())
        ]

        results.sort(key=lambda c: c.name)
        return results[:limit]
