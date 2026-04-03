"""SQLAlchemy ORM model for the `notifications` table."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, UUIDPrimaryKeyMixin
from src.domain.entities.notification import Notification


class NotificationModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> Notification:
        return Notification(
            id=self.id,
            user_id=self.user_id,
            type=self.type,
            title=self.title,
            content=self.content,
            reference_id=self.reference_id,
            read=self.read,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Notification) -> "NotificationModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type,
            title=entity.title,
            content=entity.content,
            reference_id=entity.reference_id,
            read=entity.read,
            created_at=entity.created_at,
        )
