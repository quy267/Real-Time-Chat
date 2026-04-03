"""SQLAlchemy ORM model for the `threads` table."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, UUIDPrimaryKeyMixin
from src.domain.entities.thread import Thread


class ThreadModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "threads"
    __table_args__ = (
        Index("ix_threads_channel_id", "channel_id"),
        UniqueConstraint("parent_message_id", name="uq_threads_parent_message_id"),
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> Thread:
        return Thread(
            id=self.id,
            channel_id=self.channel_id,
            parent_message_id=self.parent_message_id,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Thread) -> "ThreadModel":
        return cls(
            id=entity.id,
            channel_id=entity.channel_id,
            parent_message_id=entity.parent_message_id,
            created_at=entity.created_at,
        )
