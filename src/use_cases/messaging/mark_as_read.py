"""MarkAsReadUseCase — record the last-read message for a user in a channel."""

from src.adapters.redis.read_receipt_store import ReadReceiptStore


class MarkAsReadUseCase:
    def __init__(self, read_receipt_store: ReadReceiptStore) -> None:
        self._store = read_receipt_store

    async def execute(self, user_id: str, channel_id: str, message_id: str) -> None:
        """Mark channel as read up to message_id for user."""
        await self._store.mark_read(
            user_id=user_id,
            channel_id=channel_id,
            message_id=message_id,
        )
