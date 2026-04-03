"""DirectConversation and DirectConversationMember domain entities."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DirectConversation:
    id: uuid.UUID
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class DirectConversationMember:
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime = field(default_factory=_utcnow)
