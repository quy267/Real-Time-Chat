"""ReadReceiptStore — tracks last-read message per user per channel.

Interface is Redis-ready: keys follow `read:{user_id}:{channel_id}`.
Current implementation uses an in-memory dict for simplicity; swap
_store for an aioredis hash when Redis persistence is required.

NOTE: In-memory implementation for development. Replace with Redis-backed
implementation for multi-worker production deployment.
"""


class ReadReceiptStore:
    """In-memory store; same interface as a Redis hash adapter."""

    def __init__(self) -> None:
        # key: (user_id, channel_id) → last_read_message_id (str)
        self._store: dict[tuple[str, str], str] = {}

    def _key(self, user_id: str, channel_id: str) -> tuple[str, str]:
        return (user_id, channel_id)

    async def mark_read(self, user_id: str, channel_id: str, message_id: str) -> None:
        """Record that user has read up to message_id in channel."""
        self._store[self._key(user_id, channel_id)] = message_id

    async def get_last_read(self, user_id: str, channel_id: str) -> str | None:
        """Return the last message_id the user has read in channel, or None."""
        return self._store.get(self._key(user_id, channel_id))
