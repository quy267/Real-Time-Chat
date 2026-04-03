"""Notification domain entity — tracks user notifications for mentions, DMs, etc."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Notification:
    """Represents a notification delivered to a user."""

    id: uuid.UUID
    user_id: uuid.UUID  # recipient
    type: str  # "mention", "dm", "reaction", "channel_invite"
    title: str
    content: str
    reference_id: str | None  # message_id or channel_id
    read: bool = False
    created_at: datetime = field(default_factory=_utcnow)
