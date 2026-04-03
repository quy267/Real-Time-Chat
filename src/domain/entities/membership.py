"""Membership domain entity and MemberRole enum — user-channel relationship."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MemberRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Membership:
    user_id: uuid.UUID
    channel_id: uuid.UUID
    role: MemberRole = MemberRole.MEMBER
    joined_at: datetime = field(default_factory=_utcnow)
