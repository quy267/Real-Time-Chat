"""Unit tests for channel permission enforcement across use cases."""

import uuid

import pytest

from src.domain.entities.channel import Channel, ChannelType
from src.domain.entities.membership import MemberRole
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.use_cases.channels.delete_channel import DeleteChannelUseCase
from src.use_cases.channels.get_channel import GetChannelUseCase
from src.use_cases.channels.leave_channel import LeaveChannelUseCase
from src.use_cases.channels.update_channel import UpdateChannelUseCase
from tests.fakes.fake_channel_repository import FakeChannelRepository
from tests.fakes.fake_membership_repository import FakeMembershipRepository


@pytest.fixture
def creator_id():
    return uuid.uuid4()


@pytest.fixture
def channel_repo():
    return FakeChannelRepository()


@pytest.fixture
def membership_repo():
    return FakeMembershipRepository()


def _make_channel(creator_id: uuid.UUID, channel_type=ChannelType.PUBLIC) -> Channel:
    return Channel(
        id=uuid.uuid4(),
        name="test-channel",
        creator_id=creator_id,
        channel_type=channel_type,
    )


# --- DeleteChannelUseCase ---

async def test_only_creator_can_delete(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    other_user = uuid.uuid4()
    await membership_repo.add_member(other_user, channel.id, MemberRole.MEMBER)

    uc = DeleteChannelUseCase(channel_repo, membership_repo)

    with pytest.raises(AuthorizationError):
        await uc.execute(channel_id=str(channel.id), user_id=str(other_user))

    # Creator succeeds
    await uc.execute(channel_id=str(channel.id), user_id=str(creator_id))
    assert await channel_repo.get_by_id(channel.id) is None


# --- UpdateChannelUseCase ---

async def test_admin_can_update(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    admin_user = uuid.uuid4()
    await membership_repo.add_member(admin_user, channel.id, MemberRole.ADMIN)

    uc = UpdateChannelUseCase(channel_repo, membership_repo)
    updated = await uc.execute(
        channel_id=str(channel.id),
        user_id=str(admin_user),
        name="renamed",
        description=None,
    )
    assert updated.name == "renamed"


async def test_member_cannot_update(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    plain_member = uuid.uuid4()
    await membership_repo.add_member(plain_member, channel.id, MemberRole.MEMBER)

    uc = UpdateChannelUseCase(channel_repo, membership_repo)
    with pytest.raises(AuthorizationError):
        await uc.execute(
            channel_id=str(channel.id),
            user_id=str(plain_member),
            name="hacked",
            description=None,
        )


# --- GetChannelUseCase ---

async def test_non_member_cannot_view_private_channel(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id, ChannelType.PRIVATE)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    outsider = uuid.uuid4()
    uc = GetChannelUseCase(channel_repo, membership_repo)

    with pytest.raises(AuthorizationError):
        await uc.execute(channel_id=str(channel.id), user_id=str(outsider))


async def test_member_can_view_private_channel(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id, ChannelType.PRIVATE)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    uc = GetChannelUseCase(channel_repo, membership_repo)
    result = await uc.execute(channel_id=str(channel.id), user_id=str(creator_id))
    assert result.id == channel.id


async def test_anyone_can_view_public_channel(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id, ChannelType.PUBLIC)
    channel_repo._store[channel.id] = channel

    outsider = uuid.uuid4()
    uc = GetChannelUseCase(channel_repo, membership_repo)
    result = await uc.execute(channel_id=str(channel.id), user_id=str(outsider))
    assert result.id == channel.id


# --- LeaveChannelUseCase ---

async def test_creator_cannot_leave_own_channel(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    uc = LeaveChannelUseCase(channel_repo, membership_repo)
    with pytest.raises(AuthorizationError):
        await uc.execute(channel_id=str(channel.id), user_id=str(creator_id))


async def test_member_can_leave_channel(channel_repo, membership_repo, creator_id):
    channel = _make_channel(creator_id)
    channel_repo._store[channel.id] = channel
    await membership_repo.add_member(creator_id, channel.id, MemberRole.ADMIN)

    member_id = uuid.uuid4()
    await membership_repo.add_member(member_id, channel.id, MemberRole.MEMBER)

    uc = LeaveChannelUseCase(channel_repo, membership_repo)
    await uc.execute(channel_id=str(channel.id), user_id=str(member_id))

    assert not await membership_repo.is_member(member_id, channel.id)


async def test_leave_nonexistent_channel_raises(channel_repo, membership_repo):
    uc = LeaveChannelUseCase(channel_repo, membership_repo)
    with pytest.raises(EntityNotFoundError):
        await uc.execute(channel_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))
