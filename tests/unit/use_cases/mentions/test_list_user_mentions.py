"""Unit tests for ListUserMentionsUseCase."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.mention import Mention
from src.use_cases.mentions.list_user_mentions import ListUserMentionsUseCase
from tests.fakes.fake_mention_repository import FakeMentionRepository


def _make_mention(mentioned_user_id: uuid.UUID, offset_seconds: int = 0) -> Mention:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return Mention(
        id=uuid.uuid4(),
        message_id=uuid.uuid4(),
        mentioned_user_id=mentioned_user_id,
        created_at=base + timedelta(seconds=offset_seconds),
    )


@pytest.fixture
def repo():
    return FakeMentionRepository()


@pytest.fixture
def use_case(repo):
    return ListUserMentionsUseCase(mention_repo=repo)


@pytest.fixture
def user_id():
    return uuid.uuid4()


class TestListUserMentionsUseCase:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_mentions(self, use_case, user_id):
        result = await use_case.execute(user_id=str(user_id))
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_mentions_for_user(self, use_case, repo, user_id):
        mention = _make_mention(user_id)
        await repo.create(mention)
        result = await use_case.execute(user_id=str(user_id))
        assert len(result) == 1
        assert result[0].id == mention.id

    @pytest.mark.asyncio
    async def test_excludes_mentions_for_other_users(self, use_case, repo, user_id):
        other_user = uuid.uuid4()
        await repo.create(_make_mention(other_user))
        result = await use_case.execute(user_id=str(user_id))
        assert result == []

    @pytest.mark.asyncio
    async def test_respects_limit(self, use_case, repo, user_id):
        for i in range(5):
            await repo.create(_make_mention(user_id, offset_seconds=i))
        result = await use_case.execute(user_id=str(user_id), limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_respects_offset(self, use_case, repo, user_id):
        mentions = []
        for i in range(5):
            m = _make_mention(user_id, offset_seconds=i)
            await repo.create(m)
            mentions.append(m)
        result = await use_case.execute(user_id=str(user_id), limit=50, offset=3)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_multiple_users_isolated(self, use_case, repo):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await repo.create(_make_mention(user_a, offset_seconds=0))
        await repo.create(_make_mention(user_b, offset_seconds=1))
        result_a = await use_case.execute(user_id=str(user_a))
        result_b = await use_case.execute(user_id=str(user_b))
        assert len(result_a) == 1
        assert len(result_b) == 1
        assert result_a[0].mentioned_user_id == user_a
        assert result_b[0].mentioned_user_id == user_b
