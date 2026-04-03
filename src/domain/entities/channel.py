"""Channel domain entity and ChannelType enum."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Channel:
    id: uuid.UUID
    name: str
    creator_id: uuid.UUID
    description: str | None = None
    channel_type: ChannelType = ChannelType.PUBLIC
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
