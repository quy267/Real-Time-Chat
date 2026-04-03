"""Unit tests for SendDirectMessageUseCase."""

import uuid

import pytest

from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from src.use_cases.direct_messages.create_conversation import CreateConversationUseCase
from src.use_cases.direct_messages.send_direct_message import SendDirectMessageUseCase
from tests.fakes.fake_dm_repository import FakeDmRepository
from tests.fakes.fake_message_repository import FakeMessageRepository


@pytest.fixture
def dm_repo():
    return FakeDmRepository()


@pytest.fixture
def msg_repo():
    return FakeMessageRepository()


@pytest.fixture
async def conversation(dm_repo):
    creator = str(uuid.uuid4())
    other = str(uuid.uuid4())
    uc = CreateConversationUseCase(dm_repo)
    conv = await uc.execute(creator_id=creator, other_user_id=other)
    return conv, creator, other


async def test_send_dm_success(dm_repo, msg_repo, conversation):
    conv, creator, _ = conversation
    uc = SendDirectMessageUseCase(dm_repo, msg_repo)

    msg = await uc.execute(
        conversation_id=str(conv.id),
        user_id=creator,
        content="Hello DM",
    )

    assert msg.content == "Hello DM"
    assert msg.user_id == uuid.UUID(creator)
    assert await msg_repo.get_by_id(msg.id) is not None


async def test_send_dm_not_participant(dm_repo, msg_repo, conversation):
    conv, _, _ = conversation
    uc = SendDirectMessageUseCase(dm_repo, msg_repo)

    with pytest.raises(AuthorizationError):
        await uc.execute(
            conversation_id=str(conv.id),
            user_id=str(uuid.uuid4()),
            content="unauthorized",
        )


async def test_send_dm_conversation_not_found(dm_repo, msg_repo):
    uc = SendDirectMessageUseCase(dm_repo, msg_repo)

    with pytest.raises(EntityNotFoundError):
        await uc.execute(
            conversation_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            content="ghost",
        )


async def test_send_dm_empty_content(dm_repo, msg_repo, conversation):
    conv, creator, _ = conversation
    uc = SendDirectMessageUseCase(dm_repo, msg_repo)

    with pytest.raises(ValidationError):
        await uc.execute(
            conversation_id=str(conv.id),
            user_id=creator,
            content="  ",
        )


async def test_send_dm_other_participant_can_send(dm_repo, msg_repo, conversation):
    conv, _, other = conversation
    uc = SendDirectMessageUseCase(dm_repo, msg_repo)

    msg = await uc.execute(
        conversation_id=str(conv.id),
        user_id=other,
        content="Reply from other",
    )

    assert msg.content == "Reply from other"
