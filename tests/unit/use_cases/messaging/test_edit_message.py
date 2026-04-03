"""Unit tests for EditMessageUseCase."""

import uuid

import pytest

from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.use_cases.messaging.edit_message import EditMessageUseCase
from tests.fakes.fake_message_repository import FakeMessageRepository


@pytest.fixture
def repo():
    return FakeMessageRepository()


@pytest.fixture
def author_id():
    return str(uuid.uuid4())


@pytest.fixture
async def stored_message(repo, author_id):
    msg = Message(
        id=uuid.uuid4(),
        content="original content",
        channel_id=uuid.uuid4(),
        user_id=uuid.UUID(author_id),
    )
    return await repo.create(msg)


async def test_edit_message_success(repo, stored_message, author_id):
    uc = EditMessageUseCase(repo)
    updated = await uc.execute(
        message_id=str(stored_message.id),
        user_id=author_id,
        new_content="updated content",
    )
    assert updated.content == "updated content"
    assert updated.id == stored_message.id
    assert updated.updated_at >= stored_message.updated_at


async def test_edit_message_strips_whitespace(repo, stored_message, author_id):
    uc = EditMessageUseCase(repo)
    updated = await uc.execute(
        message_id=str(stored_message.id),
        user_id=author_id,
        new_content="  trimmed  ",
    )
    assert updated.content == "trimmed"


async def test_edit_message_not_author(repo, stored_message):
    uc = EditMessageUseCase(repo)
    other_user = str(uuid.uuid4())
    with pytest.raises(AuthorizationError):
        await uc.execute(
            message_id=str(stored_message.id),
            user_id=other_user,
            new_content="hacked",
        )


async def test_edit_message_not_found(repo, author_id):
    uc = EditMessageUseCase(repo)
    with pytest.raises(EntityNotFoundError):
        await uc.execute(
            message_id=str(uuid.uuid4()),
            user_id=author_id,
            new_content="something",
        )


async def test_edit_message_empty_content(repo, stored_message, author_id):
    uc = EditMessageUseCase(repo)
    with pytest.raises(ValidationError, match="empty"):
        await uc.execute(
            message_id=str(stored_message.id),
            user_id=author_id,
            new_content="   ",
        )
