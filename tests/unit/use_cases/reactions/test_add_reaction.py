"""Unit tests for AddReactionUseCase, RemoveReactionUseCase, ListReactionsUseCase."""

import uuid

import pytest

from src.domain.entities.message import Message
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError, ValidationError
from src.use_cases.reactions.add_reaction import AddReactionUseCase
from src.use_cases.reactions.list_reactions import ListReactionsUseCase
from src.use_cases.reactions.remove_reaction import RemoveReactionUseCase
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_reaction_repository import FakeReactionRepository


@pytest.fixture
def repos():
    return FakeReactionRepository(), FakeMessageRepository()


@pytest.fixture
def message_id():
    return str(uuid.uuid4())


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


@pytest.fixture
async def message_in_repo(repos, message_id, user_id):
    _, msg_repo = repos
    msg = Message(
        id=uuid.UUID(message_id),
        content="test message",
        channel_id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
    )
    await msg_repo.create(msg)
    return msg


# --- AddReactionUseCase ---

async def test_add_reaction_success(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    uc = AddReactionUseCase(reaction_repo, msg_repo)
    reaction = await uc.execute(message_id=message_id, user_id=user_id, emoji="👍")

    assert reaction.emoji == "👍"
    assert str(reaction.message_id) == message_id
    assert str(reaction.user_id) == user_id
    assert reaction.id is not None


async def test_add_reaction_message_not_found(repos, user_id):
    reaction_repo, msg_repo = repos
    uc = AddReactionUseCase(reaction_repo, msg_repo)
    with pytest.raises(EntityNotFoundError):
        await uc.execute(message_id=str(uuid.uuid4()), user_id=user_id, emoji="👍")


async def test_add_reaction_duplicate_rejected(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    uc = AddReactionUseCase(reaction_repo, msg_repo)
    await uc.execute(message_id=message_id, user_id=user_id, emoji="👍")

    with pytest.raises(DuplicateEntityError):
        await uc.execute(message_id=message_id, user_id=user_id, emoji="👍")


async def test_add_reaction_empty_emoji_rejected(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    uc = AddReactionUseCase(reaction_repo, msg_repo)
    with pytest.raises(ValidationError):
        await uc.execute(message_id=message_id, user_id=user_id, emoji="  ")


async def test_add_different_emoji_same_user_allowed(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    uc = AddReactionUseCase(reaction_repo, msg_repo)
    await uc.execute(message_id=message_id, user_id=user_id, emoji="👍")
    r2 = await uc.execute(message_id=message_id, user_id=user_id, emoji="❤️")
    assert r2.emoji == "❤️"


# --- RemoveReactionUseCase ---

async def test_remove_reaction_success(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    add_uc = AddReactionUseCase(reaction_repo, msg_repo)
    remove_uc = RemoveReactionUseCase(reaction_repo)

    await add_uc.execute(message_id=message_id, user_id=user_id, emoji="👍")
    await remove_uc.execute(message_id=message_id, user_id=user_id, emoji="👍")

    result = await reaction_repo.get(uuid.UUID(message_id), uuid.UUID(user_id), "👍")
    assert result is None


async def test_remove_reaction_not_found(repos, message_id, user_id):
    reaction_repo, _ = repos
    uc = RemoveReactionUseCase(reaction_repo)
    with pytest.raises(EntityNotFoundError):
        await uc.execute(message_id=message_id, user_id=user_id, emoji="👍")


# --- ListReactionsUseCase ---

async def test_list_reactions_empty(repos, message_id):
    reaction_repo, _ = repos
    uc = ListReactionsUseCase(reaction_repo)
    results = await uc.execute(message_id=message_id)
    assert results == []


async def test_list_reactions_returns_all(repos, message_id, user_id, message_in_repo):
    reaction_repo, msg_repo = repos
    add_uc = AddReactionUseCase(reaction_repo, msg_repo)
    list_uc = ListReactionsUseCase(reaction_repo)

    user2 = str(uuid.uuid4())
    await add_uc.execute(message_id=message_id, user_id=user_id, emoji="👍")
    await add_uc.execute(message_id=message_id, user_id=user_id, emoji="❤️")

    # Add message for user2 first (msg_repo already has the message, user2 just reacts)
    msg2 = Message(
        id=uuid.uuid4(),
        content="x",
        channel_id=uuid.uuid4(),
        user_id=uuid.UUID(user2),
    )
    await msg_repo.create(msg2)
    # Directly add reaction for user2 via repo
    from src.domain.entities.reaction import Reaction
    r = Reaction(id=uuid.uuid4(), message_id=uuid.UUID(message_id), user_id=uuid.UUID(user2), emoji="👍")
    await reaction_repo.add(r)

    results = await list_uc.execute(message_id=message_id)
    assert len(results) == 3
