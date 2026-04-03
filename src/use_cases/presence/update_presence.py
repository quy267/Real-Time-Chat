"""UpdatePresenceUseCase — mark a user online or offline in the presence store."""

from src.adapters.redis.presence_store import PresenceStore


class UpdatePresenceUseCase:
    def __init__(self, presence_store: PresenceStore) -> None:
        self._store = presence_store

    async def execute(self, user_id: str, online: bool) -> None:
        if online:
            await self._store.set_online(user_id)
        else:
            await self._store.set_offline(user_id)
