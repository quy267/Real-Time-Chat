"""Unit tests for CreateChannelUseCase."""

import uuid

import pytest

from src.domain.entities.channel import ChannelType
from src.domain.entities.membership import MemberRole
from src.domain.exceptions import DuplicateEntityError, ValidationError
from src.use_cases.channels.create_channel import CreateChannelUseCase
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
    return CreateChannelUseCase(channel_repo, membership_repo)


@pytest.fixture
def creator_id():
    return uuid.uuid4()


async def test_create_public_channel_success(use_case, channel_repo, membership_repo, creator_id):
    channel = await use_case.execute(
        name="general",
        description="General chat",
        channel_type="public",
        creator_id=str(creator_id),
    )
    assert channel.name == "general"
    assert channel.channel_type == ChannelType.PUBLIC
    assert channel.creator_id == creator_id

    # Creator auto-added as admin
    membership = await membership_repo.get_member(creator_id, channel.id)
    assert membership is not None
    assert membership.role == MemberRole.ADMIN


async def test_create_private_channel_success(use_case, membership_repo, creator_id):
    channel = await use_case.execute(
        name="secret",
        description="Private room",
        channel_type="private",
        creator_id=str(creator_id),
    )
    assert channel.channel_type == ChannelType.PRIVATE

    membership = await membership_repo.get_member(creator_id, channel.id)
    assert membership is not None
    assert membership.role == MemberRole.ADMIN


async def test_create_channel_duplicate_name_raises(use_case, creator_id):
    await use_case.execute(
        name="general",
        description="",
        channel_type="public",
        creator_id=str(creator_id),
    )
    with pytest.raises(DuplicateEntityError):
        await use_case.execute(
            name="general",
            description="",
            channel_type="public",
            creator_id=str(creator_id),
        )


async def test_create_channel_empty_name_raises(use_case, creator_id):
    with pytest.raises(ValidationError):
        await use_case.execute(
            name="  ",
            description="",
            channel_type="public",
            creator_id=str(creator_id),
        )


async def test_create_channel_invalid_type_raises(use_case, creator_id):
    with pytest.raises(ValidationError):
        await use_case.execute(
            name="mychan",
            description="",
            channel_type="invalid",
            creator_id=str(creator_id),
        )
