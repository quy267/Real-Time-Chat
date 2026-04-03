"""ListChannelsUseCase — return paginated channels the user belongs to."""

from uuid import UUID

from src.domain.entities.channel import Channel
from src.domain.repositories.channel_repository import ChannelRepository


class ListChannelsUseCase:
    def __init__(self, channel_repo: ChannelRepository) -> None:
        self._channel_repo = channel_repo

    async def execute(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Channel]:
        user_uuid: UUID = UUID(user_id)
        return await self._channel_repo.list_by_user(user_uuid, limit=limit, offset=offset)
