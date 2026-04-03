"""Integration tests for ReadReceiptStore — in-memory implementation."""

import uuid

import pytest

from src.adapters.redis.read_receipt_store import ReadReceiptStore


@pytest.fixture
def store():
    return ReadReceiptStore()


async def test_mark_and_get_last_read(store):
    user_id = str(uuid.uuid4())
    channel_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    await store.mark_read(user_id, channel_id, message_id)
    result = await store.get_last_read(user_id, channel_id)

    assert result == message_id


async def test_get_last_read_returns_none_when_unset(store):
    result = await store.get_last_read(str(uuid.uuid4()), str(uuid.uuid4()))
    assert result is None


async def test_mark_read_overwrites_previous(store):
    user_id = str(uuid.uuid4())
    channel_id = str(uuid.uuid4())

    msg1 = str(uuid.uuid4())
    msg2 = str(uuid.uuid4())

    await store.mark_read(user_id, channel_id, msg1)
    await store.mark_read(user_id, channel_id, msg2)

    result = await store.get_last_read(user_id, channel_id)
    assert result == msg2


async def test_different_users_isolated(store):
    channel_id = str(uuid.uuid4())
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    msg_a = str(uuid.uuid4())
    msg_b = str(uuid.uuid4())

    await store.mark_read(user_a, channel_id, msg_a)
    await store.mark_read(user_b, channel_id, msg_b)

    assert await store.get_last_read(user_a, channel_id) == msg_a
    assert await store.get_last_read(user_b, channel_id) == msg_b


async def test_different_channels_isolated(store):
    user_id = str(uuid.uuid4())
    channel_1 = str(uuid.uuid4())
    channel_2 = str(uuid.uuid4())
    msg_1 = str(uuid.uuid4())
    msg_2 = str(uuid.uuid4())

    await store.mark_read(user_id, channel_1, msg_1)
    await store.mark_read(user_id, channel_2, msg_2)

    assert await store.get_last_read(user_id, channel_1) == msg_1
    assert await store.get_last_read(user_id, channel_2) == msg_2


