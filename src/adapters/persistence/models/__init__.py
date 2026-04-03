"""Persistence models package — imports all ORM models so Alembic detects them."""

from src.adapters.persistence.models.base_model import Base
from src.adapters.persistence.models.channel_model import ChannelModel
from src.adapters.persistence.models.direct_conversation_model import (
    DirectConversationMemberModel,
    DirectConversationModel,
)
from src.adapters.persistence.models.membership_model import MembershipModel
from src.adapters.persistence.models.mention_model import MentionModel
from src.adapters.persistence.models.message_model import MessageModel
from src.adapters.persistence.models.reaction_model import ReactionModel
from src.adapters.persistence.models.thread_model import ThreadModel
from src.adapters.persistence.models.user_model import UserModel

__all__ = [
    "Base",
    "UserModel",
    "ChannelModel",
    "MessageModel",
    "ThreadModel",
    "MembershipModel",
    "DirectConversationModel",
    "DirectConversationMemberModel",
    "ReactionModel",
    "MentionModel",
]
