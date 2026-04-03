"""User domain entity — pure Python, no framework dependencies."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.value_objects.presence_status import PresenceStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    id: uuid.UUID
    username: str
    email: str
    password_hash: str
    display_name: str | None = None
    avatar_url: str | None = None
    status: PresenceStatus = PresenceStatus.OFFLINE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
