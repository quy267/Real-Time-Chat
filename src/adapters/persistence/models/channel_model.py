"""SQLAlchemy ORM model for the `channels` table."""

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.domain.entities.channel import Channel, ChannelType


class ChannelModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channels"
    __table_args__ = (Index("ix_channels_creator_id", "creator_id"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    channel_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ChannelType.PUBLIC.value
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def to_entity(self) -> Channel:
        return Channel(
            id=self.id,
            name=self.name,
            description=self.description,
            channel_type=ChannelType(self.channel_type),
            creator_id=self.creator_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Channel) -> "ChannelModel":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            channel_type=entity.channel_type.value,
            creator_id=entity.creator_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
