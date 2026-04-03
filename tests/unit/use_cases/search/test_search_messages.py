"""Unit tests for SearchMessagesUseCase."""

import uuid

import pytest

from src.domain.entities.channel import Channel
from src.domain.entities.membership import MemberRole
from src.domain.entities.message import Message
from src.use_cases.search.search_messages import SearchMessagesUseCase
from tests.fakes.fake_channel_repository import FakeChannelRepository
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository


@pytest.fixture
def repos():
    return FakeMessageRepository(), FakeChannelRepository(), FakeMembershipRepository()


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


@pytest.fixture
def channel_id():
    return str(uuid.uuid4())


@pytest.fixture
async def setup(repos, user_id, channel_id):
    msg_repo, chan_repo, mem_repo = repos
    uid = uuid.UUID(user_id)
    cid = uuid.UUID(channel_id)

    channel = Channel(id=cid, name="general", creator_id=uid)
    await chan_repo.create(channel)
    await mem_repo.add_member(uid, cid, MemberRole.MEMBER)

    msg1 = Message(id=uuid.uuid4(), content="Hello world", channel_id=cid, user_id=uid)
    msg2 = Message(id=uuid.uuid4(), content="Goodbye world", channel_id=cid, user_id=uid)
    msg3 = Message(id=uuid.uuid4(), content="Unrelated post", channel_id=cid, user_id=uid)
    await msg_repo.create(msg1)
    await msg_repo.create(msg2)
    await msg_repo.create(msg3)

    return SearchMessagesUseCase(msg_repo, chan_repo, mem_repo)


async def test_search_finds_matching_messages(setup, user_id, channel_id):
    uc = setup
    results = await uc.execute(query="world", user_id=user_id, channel_id=channel_id)
    assert len(results) == 2
    contents = {r.content for r in results}
    assert "Hello world" in contents
    assert "Goodbye world" in contents


async def test_search_case_insensitive(setup, user_id, channel_id):
    uc = setup
    results = await uc.execute(query="HELLO", user_id=user_id, channel_id=channel_id)
    assert len(results) == 1
    assert results[0].content == "Hello world"


async def test_search_no_results(setup, user_id, channel_id):
    uc = setup
    results = await uc.execute(query="zzznomatch", user_id=user_id, channel_id=channel_id)
    assert results == []


async def test_search_empty_query_returns_empty(setup, user_id, channel_id):
    uc = setup
    results = await uc.execute(query="  ", user_id=user_id, channel_id=channel_id)
    assert results == []


async def test_search_respects_channel_membership(repos, user_id):
    msg_repo, chan_repo, mem_repo = repos
    uid = uuid.UUID(user_id)
    other_channel_id = uuid.uuid4()

    # User is NOT a member of this channel
    other_channel = Channel(id=other_channel_id, name="private", creator_id=uuid.uuid4())
    await chan_repo.create(other_channel)

    msg = Message(id=uuid.uuid4(), content="Secret message", channel_id=other_channel_id, user_id=uid)
    await msg_repo.create(msg)

    uc = SearchMessagesUseCase(msg_repo, chan_repo, mem_repo)
    results = await uc.execute(query="Secret", user_id=user_id, channel_id=str(other_channel_id))
    assert results == []


async def test_search_without_channel_id_searches_all_member_channels(repos, user_id):
    msg_repo, chan_repo, mem_repo = repos
    uid = uuid.UUID(user_id)

    cid1 = uuid.uuid4()
    cid2 = uuid.uuid4()
    ch1 = Channel(id=cid1, name="ch1", creator_id=uid)
    ch2 = Channel(id=cid2, name="ch2", creator_id=uid)
    await chan_repo.create(ch1)
    await chan_repo.create(ch2)
    await mem_repo.add_member(uid, cid1, MemberRole.MEMBER)
    await mem_repo.add_member(uid, cid2, MemberRole.MEMBER)

    await msg_repo.create(Message(id=uuid.uuid4(), content="find me ch1", channel_id=cid1, user_id=uid))
    await msg_repo.create(Message(id=uuid.uuid4(), content="find me ch2", channel_id=cid2, user_id=uid))

    uc = SearchMessagesUseCase(msg_repo, chan_repo, mem_repo)
    results = await uc.execute(query="find me", user_id=user_id)
    assert len(results) == 2


async def test_search_limit_respected(repos, user_id, channel_id):
    msg_repo, chan_repo, mem_repo = repos
    uid = uuid.UUID(user_id)
    cid = uuid.UUID(channel_id)

    channel = Channel(id=cid, name="flood", creator_id=uid)
    await chan_repo.create(channel)
    await mem_repo.add_member(uid, cid, MemberRole.MEMBER)

    for i in range(10):
        await msg_repo.create(
            Message(id=uuid.uuid4(), content=f"match {i}", channel_id=cid, user_id=uid)
        )

    uc = SearchMessagesUseCase(msg_repo, chan_repo, mem_repo)
    results = await uc.execute(query="match", user_id=user_id, channel_id=channel_id, limit=3)
    assert len(results) == 3
