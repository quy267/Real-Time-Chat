"""PresenceStore — tracks online/offline user state.

In-memory implementation for dev/test. Swap to Redis hash + TTL for production.
"""

# NOTE: In-memory implementation for development. Replace with Redis-backed
# implementation for multi-worker production deployment.


class PresenceStore:
    """In-memory presence tracking. Thread-safe for single-process use."""

    def __init__(self) -> None:
        # user_id -> set of channel_ids they are online in
        self._online: dict[str, set[str]] = {}

    async def set_online(self, user_id: str, channel_id: str | None = None) -> None:
        """Mark user as online, optionally in a specific channel."""
        if user_id not in self._online:
            self._online[user_id] = set()
        if channel_id:
            self._online[user_id].add(channel_id)

    async def set_offline(self, user_id: str) -> None:
        """Remove user from online tracking entirely."""
        self._online.pop(user_id, None)

    async def is_online(self, user_id: str) -> bool:
        """Return True if user is currently online."""
        return user_id in self._online

    async def get_online_users(self, channel_id: str) -> list[str]:
        """Return list of user IDs online in a given channel."""
        return [
            uid
            for uid, channels in self._online.items()
            if channel_id in channels
        ]
