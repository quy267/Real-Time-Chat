"""Mention domain entity — tracks @mentions within messages."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Mention:
    id: uuid.UUID
    message_id: uuid.UUID
    mentioned_user_id: uuid.UUID
    created_at: datetime = field(default_factory=_utcnow)
