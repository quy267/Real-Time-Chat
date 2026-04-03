"""Unit tests for JoinChannelUseCase."""

import uuid

import pytest

from src.domain.entities.channel import Channel, ChannelType
from src.domain.entities.membership import MemberRole
from src.domain.exceptions import AuthorizationError, DuplicateEntityError, EntityNotFoundError
from src.use_cases.channels.join_channel import JoinChannelUseCase
from tests.fakes.fake_channel_repository import FakeChannelRepository
from tests.fakes.fake_membership_repository import FakeMembershipRepository


@pytest.fixture
def channel_repo():
    return FakeChannelRepository()


@pytest.fixture
def membership_repo():
    return FakeMembershipRepository()


@pytest.fixture
def use_case(channel_repo, membership_repo):
    return JoinChannelUseCase(channel_repo, membership_repo)


@pytest.fixture
def public_channel(channel_repo):
    channel = Channel(
        id=uuid.uuid4(),
        name="general",
        creator_id=uuid.uuid4(),
        channel_type=ChannelType.PUBLIC,
    )
    # Pre-store synchronously via the internal dict
    channel_repo._store[channel.id] = channel
    return channel


@pytest.fixture
def private_channel(channel_repo):
    channel = Channel(
        id=uuid.uuid4(),
        name="secret",
        creator_id=uuid.uuid4(),
        channel_type=ChannelType.PRIVATE,
    )
    channel_repo._store[channel.id] = channel
    return channel


async def test_join_public_channel_success(use_case, membership_repo, public_channel):
    user_id = uuid.uuid4()
    membership = await use_case.execute(
        channel_id=str(public_channel.id),
        user_id=str(user_id),
    )
    assert membership.user_id == user_id
    assert membership.channel_id == public_channel.id
    assert membership.role == MemberRole.MEMBER

    assert await membership_repo.is_member(user_id, public_channel.id)


async def test_join_private_channel_raises_authorization_error(use_case, private_channel):
    user_id = uuid.uuid4()
    with pytest.raises(AuthorizationError):
        await use_case.execute(
            channel_id=str(private_channel.id),
            user_id=str(user_id),
        )


async def test_join_already_member_raises_duplicate_error(use_case, membership_repo, public_channel):
    user_id = uuid.uuid4()
    await membership_repo.add_member(user_id, public_channel.id, MemberRole.MEMBER)

    with pytest.raises(DuplicateEntityError):
        await use_case.execute(
            channel_id=str(public_channel.id),
            user_id=str(user_id),
        )


async def test_join_nonexistent_channel_raises_not_found(use_case):
    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            channel_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )
