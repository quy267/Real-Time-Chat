"""Use case factory functions — wires concrete implementations for production."""

import redis.asyncio as aioredis

from src.adapters.api.bcrypt_password_service import BcryptPasswordService
from src.adapters.api.jwt_token_service import JwtTokenService
from src.adapters.persistence.repositories.sqlalchemy_channel_repository import SQLAlchemyChannelRepository
from src.adapters.persistence.repositories.sqlalchemy_membership_repository import SQLAlchemyMembershipRepository
from src.adapters.persistence.repositories.sqlalchemy_message_repository import SQLAlchemyMessageRepository
from src.adapters.persistence.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.adapters.redis.presence_store import PresenceStore
from src.adapters.redis.read_receipt_store import ReadReceiptStore
from src.adapters.redis.token_blacklist import TokenBlacklist
from src.infrastructure.config import settings
from src.use_cases.auth.login_user import LoginUserUseCase
from src.use_cases.auth.logout_user import LogoutUserUseCase
from src.use_cases.auth.refresh_token import RefreshTokenUseCase
from src.use_cases.auth.register_user import RegisterUserUseCase
from src.use_cases.channels.create_channel import CreateChannelUseCase
from src.use_cases.channels.delete_channel import DeleteChannelUseCase
from src.use_cases.channels.get_channel import GetChannelUseCase
from src.use_cases.channels.join_channel import JoinChannelUseCase
from src.use_cases.channels.leave_channel import LeaveChannelUseCase
from src.use_cases.channels.list_channels import ListChannelsUseCase
from src.use_cases.channels.list_members import ListMembersUseCase
from src.use_cases.channels.update_channel import UpdateChannelUseCase
from src.use_cases.direct_messages.create_conversation import CreateConversationUseCase
from src.use_cases.direct_messages.get_dm_history import GetDmHistoryUseCase
from src.use_cases.direct_messages.list_conversations import ListConversationsUseCase
from src.use_cases.direct_messages.send_direct_message import SendDirectMessageUseCase
from src.use_cases.mentions.list_user_mentions import ListUserMentionsUseCase
from src.use_cases.mentions.parse_mentions import ParseMentionsUseCase
from src.use_cases.messaging.delete_message import DeleteMessageUseCase
from src.use_cases.messaging.edit_message import EditMessageUseCase
from src.use_cases.messaging.get_message_history import GetMessageHistoryUseCase
from src.use_cases.messaging.get_unread_count import GetUnreadCountUseCase
from src.use_cases.messaging.mark_as_read import MarkAsReadUseCase
from src.use_cases.messaging.send_message import SendMessageUseCase
from src.use_cases.presence.get_online_users import GetOnlineUsersUseCase
from src.use_cases.presence.update_presence import UpdatePresenceUseCase
from src.use_cases.threads.create_thread import CreateThreadUseCase
from src.use_cases.threads.get_thread_replies import GetThreadRepliesUseCase
from src.use_cases.threads.reply_to_thread import ReplyToThreadUseCase

# Stateless service singletons — safe to share across requests
_jwt_token_service = JwtTokenService()
_bcrypt_password_service = BcryptPasswordService()


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def _get_token_blacklist() -> TokenBlacklist:
    return TokenBlacklist(_get_redis())


def _get_channel_repo() -> SQLAlchemyChannelRepository:
    from src.adapters.persistence.database import async_session_factory

    return SQLAlchemyChannelRepository(async_session_factory())


def _get_membership_repo() -> SQLAlchemyMembershipRepository:
    from src.adapters.persistence.database import async_session_factory

    return SQLAlchemyMembershipRepository(async_session_factory())


# --- Auth use cases ---

def get_register_use_case() -> RegisterUserUseCase:
    from src.adapters.persistence.database import async_session_factory

    session = async_session_factory()
    return RegisterUserUseCase(
        SQLAlchemyUserRepository(session),
        _bcrypt_password_service,
        _jwt_token_service,
    )


def get_login_use_case() -> LoginUserUseCase:
    from src.adapters.persistence.database import async_session_factory

    session = async_session_factory()
    return LoginUserUseCase(
        SQLAlchemyUserRepository(session),
        _bcrypt_password_service,
        _jwt_token_service,
    )


def get_refresh_use_case() -> RefreshTokenUseCase:
    return RefreshTokenUseCase(_get_token_blacklist(), _jwt_token_service)


def get_logout_use_case() -> LogoutUserUseCase:
    return LogoutUserUseCase(_get_token_blacklist())


# --- Channel use cases ---

def get_create_channel_use_case() -> CreateChannelUseCase:
    return CreateChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_list_channels_use_case() -> ListChannelsUseCase:
    return ListChannelsUseCase(_get_channel_repo())


def get_get_channel_use_case() -> GetChannelUseCase:
    return GetChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_update_channel_use_case() -> UpdateChannelUseCase:
    return UpdateChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_delete_channel_use_case() -> DeleteChannelUseCase:
    return DeleteChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_join_channel_use_case() -> JoinChannelUseCase:
    return JoinChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_leave_channel_use_case() -> LeaveChannelUseCase:
    return LeaveChannelUseCase(_get_channel_repo(), _get_membership_repo())


def get_list_members_use_case() -> ListMembersUseCase:
    return ListMembersUseCase(_get_channel_repo(), _get_membership_repo())


# --- Message use cases ---

def _get_message_repo() -> SQLAlchemyMessageRepository:
    from src.adapters.persistence.database import async_session_factory

    return SQLAlchemyMessageRepository(async_session_factory())


def get_send_message_use_case() -> SendMessageUseCase:
    return SendMessageUseCase(_get_message_repo(), _get_membership_repo())


def get_edit_message_use_case() -> EditMessageUseCase:
    return EditMessageUseCase(_get_message_repo())


def get_delete_message_use_case() -> DeleteMessageUseCase:
    return DeleteMessageUseCase(_get_message_repo())


def get_get_message_history_use_case() -> GetMessageHistoryUseCase:
    return GetMessageHistoryUseCase(_get_message_repo(), _get_membership_repo())


# --- Presence use cases ---

_presence_store = PresenceStore()


def get_update_presence_use_case() -> UpdatePresenceUseCase:
    return UpdatePresenceUseCase(_presence_store)


def get_get_online_users_use_case() -> GetOnlineUsersUseCase:
    return GetOnlineUsersUseCase(_presence_store)


# --- Thread use cases ---

def _get_thread_repo():
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_thread_repository import SQLAlchemyThreadRepository

    return SQLAlchemyThreadRepository(async_session_factory())


def get_create_thread_use_case() -> CreateThreadUseCase:
    return CreateThreadUseCase(_get_thread_repo(), _get_message_repo())


def get_reply_to_thread_use_case() -> ReplyToThreadUseCase:
    return ReplyToThreadUseCase(_get_thread_repo(), _get_message_repo(), _get_membership_repo())


def get_thread_replies_use_case() -> GetThreadRepliesUseCase:
    return GetThreadRepliesUseCase(_get_thread_repo(), _get_message_repo())


# --- DM use cases ---

def _get_dm_repo():
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_dm_repository import SQLAlchemyDmRepository

    return SQLAlchemyDmRepository(async_session_factory())


def get_create_conversation_use_case() -> CreateConversationUseCase:
    return CreateConversationUseCase(_get_dm_repo())


def get_list_conversations_use_case() -> ListConversationsUseCase:
    return ListConversationsUseCase(_get_dm_repo())


def get_send_dm_use_case() -> SendDirectMessageUseCase:
    return SendDirectMessageUseCase(_get_dm_repo(), _get_message_repo())


def get_dm_history_use_case() -> GetDmHistoryUseCase:
    return GetDmHistoryUseCase(_get_dm_repo(), _get_message_repo())


# --- Mention use cases ---

def _get_mention_repo():
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_mention_repository import SQLAlchemyMentionRepository

    return SQLAlchemyMentionRepository(async_session_factory())


def _get_user_repo():
    from src.adapters.persistence.database import async_session_factory

    return SQLAlchemyUserRepository(async_session_factory())


def get_parse_mentions_use_case() -> ParseMentionsUseCase:
    return ParseMentionsUseCase(_get_mention_repo(), _get_user_repo())


def get_list_mentions_use_case() -> ListUserMentionsUseCase:
    return ListUserMentionsUseCase(_get_mention_repo())


# --- Read receipt use cases ---

_read_receipt_store = ReadReceiptStore()


def get_mark_as_read_use_case() -> MarkAsReadUseCase:
    return MarkAsReadUseCase(_read_receipt_store)


def get_unread_count_use_case() -> GetUnreadCountUseCase:
    return GetUnreadCountUseCase(_read_receipt_store, _get_message_repo())


# --- Search use cases ---

def get_search_messages_use_case():
    from src.use_cases.search.search_messages import SearchMessagesUseCase

    return SearchMessagesUseCase(_get_message_repo(), _get_channel_repo(), _get_membership_repo())


def get_search_channels_use_case():
    from src.use_cases.search.search_channels import SearchChannelsUseCase

    return SearchChannelsUseCase(_get_channel_repo())


# --- Reaction use cases ---

def _get_reaction_repo():
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_reaction_repository import SQLAlchemyReactionRepository

    return SQLAlchemyReactionRepository(async_session_factory())


def get_add_reaction_use_case():
    from src.use_cases.reactions.add_reaction import AddReactionUseCase

    return AddReactionUseCase(_get_reaction_repo(), _get_message_repo())


def get_remove_reaction_use_case():
    from src.use_cases.reactions.remove_reaction import RemoveReactionUseCase

    return RemoveReactionUseCase(_get_reaction_repo())


def get_list_reactions_use_case():
    from src.use_cases.reactions.list_reactions import ListReactionsUseCase

    return ListReactionsUseCase(_get_reaction_repo())


# --- File upload ---

def get_upload_file_use_case():
    from src.adapters.storage.local_file_storage import LocalFileStorage
    from src.use_cases.files.upload_file import UploadFileUseCase

    storage = LocalFileStorage(settings.upload_dir, settings.max_upload_size_mb * 1024 * 1024)
    return UploadFileUseCase(storage)


# --- User profile ---

def get_user_profile_use_case():
    from src.use_cases.users.get_user_profile import GetUserProfileUseCase

    return GetUserProfileUseCase(_get_user_repo())


def get_update_user_profile_use_case():
    from src.use_cases.users.update_user_profile import UpdateUserProfileUseCase

    return UpdateUserProfileUseCase(_get_user_repo())


# --- Notification use cases ---

def _get_notification_repo():
    from src.adapters.persistence.database import async_session_factory
    from src.adapters.persistence.repositories.sqlalchemy_notification_repository import (
        SQLAlchemyNotificationRepository,
    )

    return SQLAlchemyNotificationRepository(async_session_factory())


def get_notification_repo():
    return _get_notification_repo()


def get_list_notifications_use_case():
    from src.use_cases.notifications.list_notifications import ListNotificationsUseCase

    return ListNotificationsUseCase(_get_notification_repo())


def get_mark_notification_read_use_case():
    from src.use_cases.notifications.mark_notification_read import MarkNotificationReadUseCase

    return MarkNotificationReadUseCase(_get_notification_repo())


def get_mark_all_read_use_case():
    from src.use_cases.notifications.mark_all_read import MarkAllReadUseCase

    return MarkAllReadUseCase(_get_notification_repo())
