"""Unit tests for ReplyToThreadUseCase."""

import uuid

import pytest

from src.domain.entities.membership import MemberRole
from src.domain.entities.thread import Thread
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.use_cases.threads.reply_to_thread import ReplyToThreadUseCase
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_thread_repository import FakeThreadRepository


def _make_thread(channel_id: uuid.UUID | None = None) -> Thread:
    return Thread(
        id=uuid.uuid4(),
        channel_id=channel_id or uuid.uuid4(),
        parent_message_id=uuid.uuid4(),
    )


@pytest.fixture
def channel_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
async def setup(channel_id, user_id):
    thread_repo = FakeThreadRepository()
    msg_repo = FakeMessageRepository()
    mem_repo = FakeMembershipRepository()
    thread = await thread_repo.create(_make_thread(channel_id))
    await mem_repo.add_member(user_id, channel_id, MemberRole.MEMBER)
    uc = ReplyToThreadUseCase(thread_repo, msg_repo, mem_repo)
    return uc, thread, msg_repo


async def test_reply_success(setup, user_id):
    uc, thread, msg_repo = setup
    msg = await uc.execute(
        thread_id=str(thread.id),
        user_id=str(user_id),
        content="A reply",
    )
    assert msg.content == "A reply"
    assert msg.thread_id == thread.id
    assert msg.channel_id == thread.channel_id
    assert await msg_repo.get_by_id(msg.id) is not None


async def test_reply_thread_not_found(setup, user_id):
    uc, _, _ = setup
    with pytest.raises(EntityNotFoundError):
        await uc.execute(
            thread_id=str(uuid.uuid4()),
            user_id=str(user_id),
            content="reply",
        )


async def test_reply_not_a_member(setup):
    uc, thread, _ = setup
    non_member = uuid.uuid4()
    with pytest.raises(AuthorizationError):
        await uc.execute(
            thread_id=str(thread.id),
            user_id=str(non_member),
            content="reply",
        )


async def test_reply_empty_content(setup, user_id):
    uc, thread, _ = setup
    with pytest.raises(ValidationError):
        await uc.execute(
            thread_id=str(thread.id),
            user_id=str(user_id),
            content="   ",
        )


async def test_reply_strips_whitespace(setup, user_id):
    uc, thread, _ = setup
    msg = await uc.execute(
        thread_id=str(thread.id),
        user_id=str(user_id),
        content="  trimmed  ",
    )
    assert msg.content == "trimmed"
