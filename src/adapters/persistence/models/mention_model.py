"""SQLAlchemy ORM model for the `mentions` table."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, UUIDPrimaryKeyMixin
from src.domain.entities.mention import Mention


class MentionModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "mentions"
    __table_args__ = (
        Index("ix_mentions_mentioned_user_id", "mentioned_user_id"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentioned_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> Mention:
        return Mention(
            id=self.id,
            message_id=self.message_id,
            mentioned_user_id=self.mentioned_user_id,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Mention) -> "MentionModel":
        return cls(
            id=entity.id,
            message_id=entity.message_id,
            mentioned_user_id=entity.mentioned_user_id,
            created_at=entity.created_at,
        )
