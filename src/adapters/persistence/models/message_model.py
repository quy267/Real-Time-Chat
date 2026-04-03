"""SQLAlchemy ORM model for the `messages` table."""

import uuid

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.domain.entities.message import Message


class MessageModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_channel_created", "channel_id", "created_at"),
        Index("ix_messages_user_id", "user_id"),
        Index("ix_messages_thread_id", "thread_id"),
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    thread_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_entity(self) -> Message:
        return Message(
            id=self.id,
            content=self.content,
            channel_id=self.channel_id,
            user_id=self.user_id,
            thread_id=self.thread_id,
            file_url=self.file_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageModel":
        return cls(
            id=entity.id,
            content=entity.content,
            channel_id=entity.channel_id,
            user_id=entity.user_id,
            thread_id=entity.thread_id,
            file_url=entity.file_url,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
