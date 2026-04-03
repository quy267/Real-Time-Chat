"""Reaction domain entity — emoji reaction on a message."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Reaction:
    id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    emoji: str
    created_at: datetime = field(default_factory=_utcnow)
