"""Unit tests for CreateThreadUseCase."""

import uuid

import pytest

from src.domain.entities.message import Message
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from src.use_cases.threads.create_thread import CreateThreadUseCase
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_thread_repository import FakeThreadRepository


def _make_message(channel_id: uuid.UUID | None = None) -> Message:
    return Message(
        id=uuid.uuid4(),
        content="hello",
        channel_id=channel_id or uuid.uuid4(),
        user_id=uuid.uuid4(),
    )


@pytest.fixture
def repos():
    return FakeThreadRepository(), FakeMessageRepository()


async def test_create_thread_success(repos):
    thread_repo, msg_repo = repos
    msg = await msg_repo.create(_make_message())
    uc = CreateThreadUseCase(thread_repo, msg_repo)

    thread = await uc.execute(parent_message_id=str(msg.id), user_id=str(uuid.uuid4()))

    assert thread.id is not None
    assert thread.parent_message_id == msg.id
    assert thread.channel_id == msg.channel_id


async def test_create_thread_message_not_found(repos):
    thread_repo, msg_repo = repos
    uc = CreateThreadUseCase(thread_repo, msg_repo)

    with pytest.raises(EntityNotFoundError):
        await uc.execute(parent_message_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))


async def test_create_thread_duplicate_raises(repos):
    thread_repo, msg_repo = repos
    msg = await msg_repo.create(_make_message())
    uc = CreateThreadUseCase(thread_repo, msg_repo)

    await uc.execute(parent_message_id=str(msg.id), user_id=str(uuid.uuid4()))

    with pytest.raises(DuplicateEntityError):
        await uc.execute(parent_message_id=str(msg.id), user_id=str(uuid.uuid4()))


async def test_create_thread_stored_in_repo(repos):
    thread_repo, msg_repo = repos
    msg = await msg_repo.create(_make_message())
    uc = CreateThreadUseCase(thread_repo, msg_repo)

    thread = await uc.execute(parent_message_id=str(msg.id), user_id=str(uuid.uuid4()))

    stored = await thread_repo.get_by_id(thread.id)
    assert stored is not None
    assert stored.id == thread.id
