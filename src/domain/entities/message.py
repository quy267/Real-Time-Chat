"""Message domain entity — represents a chat message in a channel."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Message:
    id: uuid.UUID
    content: str
    channel_id: uuid.UUID
    user_id: uuid.UUID
    thread_id: uuid.UUID | None = None
    file_url: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
