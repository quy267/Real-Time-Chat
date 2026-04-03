"""Unit tests for ParseMentionsUseCase."""

import uuid

import pytest

from src.domain.entities.user import User
from src.use_cases.mentions.parse_mentions import ParseMentionsUseCase
from tests.fakes.fake_mention_repository import FakeMentionRepository
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_user(username: str) -> User:
    return User(
        id=uuid.uuid4(),
        username=username,
        email=f"{username}@example.com",
        password_hash="hash",
    )


@pytest.fixture
def repos():
    return FakeMentionRepository(), FakeUserRepository()


async def test_parse_single_mention(repos):
    mention_repo, user_repo = repos
    alice = await user_repo.create(_make_user("alice"))
    uc = ParseMentionsUseCase(mention_repo, user_repo)

    mentions = await uc.execute(
        content="Hello @alice how are you?",
        message_id=str(uuid.uuid4()),
    )

    assert len(mentions) == 1
    assert mentions[0].mentioned_user_id == alice.id


async def test_parse_multiple_mentions(repos):
    mention_repo, user_repo = repos
    alice = await user_repo.create(_make_user("alice"))
    bob = await user_repo.create(_make_user("bob"))
    uc = ParseMentionsUseCase(mention_repo, user_repo)

    mentions = await uc.execute(
        content="@alice and @bob please review",
        message_id=str(uuid.uuid4()),
    )

    mentioned_ids = {m.mentioned_user_id for m in mentions}
    assert mentioned_ids == {alice.id, bob.id}


async def test_nonexistent_username_ignored(repos):
    mention_repo, user_repo = repos
    uc = ParseMentionsUseCase(mention_repo, user_repo)

    mentions = await uc.execute(
        content="Hello @ghost nobody here",
        message_id=str(uuid.uuid4()),
    )

    assert mentions == []


async def test_no_mentions_returns_empty(repos):
    mention_repo, user_repo = repos
    uc = ParseMentionsUseCase(mention_repo, user_repo)

    mentions = await uc.execute(
        content="Hello everyone, no mentions here",
        message_id=str(uuid.uuid4()),
    )

    assert mentions == []


async def test_duplicate_mention_creates_one_record(repos):
    mention_repo, user_repo = repos
    alice = await user_repo.create(_make_user("alice"))
    uc = ParseMentionsUseCase(mention_repo, user_repo)

    mentions = await uc.execute(
        content="@alice @alice double mention",
        message_id=str(uuid.uuid4()),
    )

    assert len(mentions) == 1
    assert mentions[0].mentioned_user_id == alice.id


async def test_mentions_persisted_in_repo(repos):
    mention_repo, user_repo = repos
    alice = await user_repo.create(_make_user("alice"))
    uc = ParseMentionsUseCase(mention_repo, user_repo)
    msg_id = str(uuid.uuid4())

    await uc.execute(content="Hey @alice!", message_id=msg_id)

    stored = await mention_repo.list_by_user(alice.id)
    assert len(stored) == 1
    assert str(stored[0].message_id) == msg_id
