"""Unit tests for CreateConversationUseCase."""

import uuid

import pytest

from src.domain.exceptions import ValidationError
from src.use_cases.direct_messages.create_conversation import CreateConversationUseCase
from tests.fakes.fake_dm_repository import FakeDmRepository


@pytest.fixture
def dm_repo():
    return FakeDmRepository()


async def test_create_conversation_success(dm_repo):
    uc = CreateConversationUseCase(dm_repo)
    creator = str(uuid.uuid4())
    other = str(uuid.uuid4())

    conv = await uc.execute(creator_id=creator, other_user_id=other)

    assert conv.id is not None
    assert await dm_repo.is_participant(conv.id, uuid.UUID(creator))
    assert await dm_repo.is_participant(conv.id, uuid.UUID(other))


async def test_create_conversation_returns_existing(dm_repo):
    uc = CreateConversationUseCase(dm_repo)
    creator = str(uuid.uuid4())
    other = str(uuid.uuid4())

    conv1 = await uc.execute(creator_id=creator, other_user_id=other)
    conv2 = await uc.execute(creator_id=creator, other_user_id=other)

    assert conv1.id == conv2.id


async def test_create_conversation_existing_reversed_order(dm_repo):
    """Should return same conversation even when caller and other are swapped."""
    uc = CreateConversationUseCase(dm_repo)
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())

    conv1 = await uc.execute(creator_id=user_a, other_user_id=user_b)
    conv2 = await uc.execute(creator_id=user_b, other_user_id=user_a)

    assert conv1.id == conv2.id


async def test_self_dm_rejected(dm_repo):
    uc = CreateConversationUseCase(dm_repo)
    user = str(uuid.uuid4())

    with pytest.raises(ValidationError, match="yourself"):
        await uc.execute(creator_id=user, other_user_id=user)
