"""GetOnlineUsersUseCase — return list of online user IDs for a channel."""

from src.adapters.redis.presence_store import PresenceStore


class GetOnlineUsersUseCase:
    def __init__(self, presence_store: PresenceStore) -> None:
        self._store = presence_store

    async def execute(self, channel_id: str) -> list[str]:
        return await self._store.get_online_users(channel_id)
