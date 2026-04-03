"""Unit tests for SendMessageUseCase."""

import uuid

import pytest

from src.domain.entities.membership import MemberRole
from src.domain.exceptions import AuthorizationError, ValidationError
from src.use_cases.messaging.send_message import MAX_CONTENT_LENGTH, SendMessageUseCase
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository


@pytest.fixture
def repos():
    return FakeMessageRepository(), FakeMembershipRepository()


@pytest.fixture
def channel_id():
    return str(uuid.uuid4())


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


@pytest.fixture
async def member_uc(repos, channel_id, user_id):
    """Use case with the user already a member of the channel."""
    msg_repo, mem_repo = repos
    await mem_repo.add_member(uuid.UUID(user_id), uuid.UUID(channel_id), MemberRole.MEMBER)
    return SendMessageUseCase(msg_repo, mem_repo), msg_repo


async def test_send_message_success(member_uc, channel_id, user_id):
    uc, repo = member_uc
    msg = await uc.execute(content="Hello world", channel_id=channel_id, user_id=user_id)

    assert msg.content == "Hello world"
    assert str(msg.channel_id) == channel_id
    assert str(msg.user_id) == user_id
    assert msg.id is not None
    assert await repo.get_by_id(msg.id) is not None


async def test_send_message_strips_whitespace(member_uc, channel_id, user_id):
    uc, _ = member_uc
    msg = await uc.execute(content="  hello  ", channel_id=channel_id, user_id=user_id)
    assert msg.content == "hello"


async def test_send_message_empty_content(member_uc, channel_id, user_id):
    uc, _ = member_uc
    with pytest.raises(ValidationError, match="empty"):
        await uc.execute(content="   ", channel_id=channel_id, user_id=user_id)


async def test_send_message_content_too_long(member_uc, channel_id, user_id):
    uc, _ = member_uc
    with pytest.raises(ValidationError, match=str(MAX_CONTENT_LENGTH)):
        await uc.execute(content="x" * (MAX_CONTENT_LENGTH + 1), channel_id=channel_id, user_id=user_id)


async def test_send_message_not_a_member(repos, channel_id, user_id):
    msg_repo, mem_repo = repos
    uc = SendMessageUseCase(msg_repo, mem_repo)
    with pytest.raises(AuthorizationError):
        await uc.execute(content="hello", channel_id=channel_id, user_id=user_id)


async def test_send_message_with_thread_id(member_uc, channel_id, user_id):
    uc, _ = member_uc
    thread_id = str(uuid.uuid4())
    msg = await uc.execute(content="reply", channel_id=channel_id, user_id=user_id, thread_id=thread_id)
    assert str(msg.thread_id) == thread_id


async def test_send_message_with_file_url(member_uc, channel_id, user_id):
    uc, _ = member_uc
    msg = await uc.execute(
        content="see attachment",
        channel_id=channel_id,
        user_id=user_id,
        file_url="https://example.com/file.png",
    )
    assert msg.file_url == "https://example.com/file.png"
