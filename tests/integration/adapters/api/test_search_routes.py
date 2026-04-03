"""Integration tests for search API routes using fake repositories."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_channel_repository import FakeChannelRepository
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, channel_repo, membership_repo, message_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.channel_routes import router as channel_router
    from src.adapters.api.routes.search_routes import router as search_router
    from src.domain.exceptions import (
        AuthenticationError,
        AuthorizationError,
        DuplicateEntityError,
        EntityNotFoundError,
        ValidationError,
    )
    from src.use_cases.auth.login_user import LoginUserUseCase
    from src.use_cases.auth.logout_user import LogoutUserUseCase
    from src.use_cases.auth.refresh_token import RefreshTokenUseCase
    from src.use_cases.auth.register_user import RegisterUserUseCase
    from src.use_cases.channels.create_channel import CreateChannelUseCase
    from src.use_cases.channels.get_channel import GetChannelUseCase
    from src.use_cases.channels.join_channel import JoinChannelUseCase
    from src.use_cases.channels.list_channels import ListChannelsUseCase
    from src.use_cases.search.search_channels import SearchChannelsUseCase
    from src.use_cases.search.search_messages import SearchMessagesUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_create_channel_use_case = lambda: CreateChannelUseCase(channel_repo, membership_repo)
    deps.get_list_channels_use_case = lambda: ListChannelsUseCase(channel_repo)
    deps.get_get_channel_use_case = lambda: GetChannelUseCase(channel_repo, membership_repo)
    deps.get_join_channel_use_case = lambda: JoinChannelUseCase(channel_repo, membership_repo)
    deps.get_search_messages_use_case = lambda: SearchMessagesUseCase(
        message_repo, channel_repo, membership_repo
    )
    deps.get_search_channels_use_case = lambda: SearchChannelsUseCase(channel_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(channel_router)
    app.include_router(search_router)

    @app.exception_handler(DuplicateEntityError)
    async def dup_handler(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def val_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(EntityNotFoundError)
    async def nf_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    return app


@pytest.fixture
def stores():
    return (
        FakeUserRepository(),
        FakeChannelRepository(),
        FakeMembershipRepository(),
        FakeMessageRepository(),
        FakeTokenBlacklist(),
    )


@pytest.fixture
async def search_client(stores) -> AsyncGenerator[tuple[AsyncClient, str, str], None]:
    """Yields (client, token, channel_id) with one message already seeded."""
    user_repo, channel_repo, membership_repo, message_repo, blacklist = stores
    app = _make_app(user_repo, channel_repo, membership_repo, message_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]

        chan = await ac.post(
            "/api/channels",
            json={"name": "general", "description": "General chat", "channel_type": "public"},
            headers={"Authorization": f"Bearer {token}"},
        )
        channel_id = chan.json()["id"]

        # Seed a message directly into the repo
        from src.adapters.api.jwt_utils import decode_token
        from src.domain.entities.message import Message

        payload = decode_token(token)
        user_id = payload["sub"]
        msg = Message(
            id=uuid.uuid4(),
            content="Hello world from integration test",
            channel_id=uuid.UUID(channel_id),
            user_id=uuid.UUID(user_id),
        )
        await message_repo.create(msg)
        yield ac, token, channel_id


async def test_search_messages_finds_match(search_client):
    client, token, channel_id = search_client
    resp = await client.get(
        "/api/search/messages",
        params={"q": "Hello", "channel_id": channel_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "Hello" in data["items"][0]["content"]


async def test_search_messages_no_match(search_client):
    client, token, channel_id = search_client
    resp = await client.get(
        "/api/search/messages",
        params={"q": "zzznomatch", "channel_id": channel_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_search_messages_non_member_channel_returns_empty(stores):
    user_repo, channel_repo, membership_repo, message_repo, blacklist = stores
    app = _make_app(user_repo, channel_repo, membership_repo, message_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "owner", "email": "owner@example.com", "password": "pass1234"},
        )
        owner_token = r1.json()["access_token"]

        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "stranger", "email": "stranger@example.com", "password": "pass1234"},
        )
        stranger_token = r2.json()["access_token"]

        chan = await ac.post(
            "/api/channels",
            json={"name": "private-chan", "description": "", "channel_type": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        channel_id = chan.json()["id"]

        resp = await ac.get(
            "/api/search/messages",
            params={"q": "anything", "channel_id": channel_id},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0  # empty — not a member


async def test_search_channels_finds_by_name(search_client):
    client, token, _ = search_client
    resp = await client.get(
        "/api/search/channels",
        params={"q": "general"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    names = [item["name"] for item in data["items"]]
    assert "general" in names


async def test_search_channels_no_match(search_client):
    client, token, _ = search_client
    resp = await client.get(
        "/api/search/channels",
        params={"q": "zzznomatch"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_search_requires_auth(stores):
    user_repo, channel_repo, membership_repo, message_repo, blacklist = stores
    app = _make_app(user_repo, channel_repo, membership_repo, message_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/search/messages", params={"q": "hello"})
        assert resp.status_code == 422  # missing auth header
