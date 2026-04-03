"""Thread domain entity — groups replies under a parent message."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Thread:
    id: uuid.UUID
    channel_id: uuid.UUID
    parent_message_id: uuid.UUID
    created_at: datetime = field(default_factory=_utcnow)
