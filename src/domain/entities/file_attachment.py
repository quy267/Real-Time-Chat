"""FileAttachment domain entity — metadata for an uploaded file."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FileAttachment:
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    url: str
    user_id: uuid.UUID
    created_at: datetime = field(default_factory=_utcnow)
