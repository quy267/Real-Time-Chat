"""Integration tests for channel API routes using fake repositories."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_channel_repository import FakeChannelRepository
from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(
    user_repo: FakeUserRepository,
    channel_repo: FakeChannelRepository,
    membership_repo: FakeMembershipRepository,
    blacklist: FakeTokenBlacklist,
):
    """Build FastAPI app wired entirely to in-memory fakes."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.channel_routes import router as channel_router
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
    from src.use_cases.channels.delete_channel import DeleteChannelUseCase
    from src.use_cases.channels.get_channel import GetChannelUseCase
    from src.use_cases.channels.join_channel import JoinChannelUseCase
    from src.use_cases.channels.leave_channel import LeaveChannelUseCase
    from src.use_cases.channels.list_channels import ListChannelsUseCase
    from src.use_cases.channels.list_members import ListMembersUseCase
    from src.use_cases.channels.update_channel import UpdateChannelUseCase

    app = FastAPI()

    import src.adapters.api.dependencies as deps

    # Auth wiring
    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)

    # Channel wiring
    deps.get_create_channel_use_case = lambda: CreateChannelUseCase(channel_repo, membership_repo)
    deps.get_list_channels_use_case = lambda: ListChannelsUseCase(channel_repo)
    deps.get_get_channel_use_case = lambda: GetChannelUseCase(channel_repo, membership_repo)
    deps.get_update_channel_use_case = lambda: UpdateChannelUseCase(channel_repo, membership_repo)
    deps.get_delete_channel_use_case = lambda: DeleteChannelUseCase(channel_repo, membership_repo)
    deps.get_join_channel_use_case = lambda: JoinChannelUseCase(channel_repo, membership_repo)
    deps.get_leave_channel_use_case = lambda: LeaveChannelUseCase(channel_repo, membership_repo)
    deps.get_list_members_use_case = lambda: ListMembersUseCase(channel_repo, membership_repo)

    app.include_router(auth_router)
    app.include_router(channel_router)

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_handler(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    return app


@pytest.fixture
def repos():
    return (
        FakeUserRepository(),
        FakeChannelRepository(),
        FakeMembershipRepository(),
        FakeTokenBlacklist(),
    )


@pytest.fixture
async def client(repos) -> AsyncGenerator[AsyncClient, None]:
    user_repo, channel_repo, membership_repo, blacklist = repos
    app = _make_app(user_repo, channel_repo, membership_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(repos) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    """Client pre-authenticated as a registered user; yields (client, access_token)."""
    user_repo, channel_repo, membership_repo, blacklist = repos
    app = _make_app(user_repo, channel_repo, membership_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "securepass"},
        )
        token = reg.json()["access_token"]
        yield ac, token


# --- Tests ---

async def test_create_channel_returns_201(auth_client):
    client, token = auth_client
    resp = await client.post(
        "/api/channels",
        json={"name": "general", "description": "Hello world", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "general"
    assert data["channel_type"] == "public"
    assert "id" in data


async def test_list_channels_returns_user_channels(auth_client):
    client, token = auth_client
    await client.post(
        "/api/channels",
        json={"name": "dev", "description": "", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        "/api/channels",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    names = [item["name"] for item in data["items"]]
    assert "dev" in names


async def test_get_channel_returns_channel(auth_client):
    client, token = auth_client
    created = await client.post(
        "/api/channels",
        json={"name": "random", "description": "", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    channel_id = created.json()["id"]
    resp = await client.get(
        f"/api/channels/{channel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == channel_id


async def test_join_and_leave_channel(repos):
    """Two separate users: creator creates channel, second user joins then leaves."""
    user_repo, channel_repo, membership_repo, blacklist = repos
    app = _make_app(user_repo, channel_repo, membership_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register creator
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "creator", "email": "creator@example.com", "password": "securepass"},
        )
        creator_token = r1.json()["access_token"]

        # Register joiner
        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "joiner", "email": "joiner@example.com", "password": "securepass"},
        )
        joiner_token = r2.json()["access_token"]

        me_resp = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {joiner_token}"},
        )
        joiner_user_id = me_resp.json()["user_id"]

        # Creator creates channel
        chan = await ac.post(
            "/api/channels",
            json={"name": "pub", "description": "", "channel_type": "public"},
            headers={"Authorization": f"Bearer {creator_token}"},
        )
        channel_id = chan.json()["id"]

        # Joiner joins
        join_resp = await ac.post(
            f"/api/channels/{channel_id}/members",
            headers={"Authorization": f"Bearer {joiner_token}"},
        )
        assert join_resp.status_code == 201
        assert join_resp.json()["role"] == "member"

        # Joiner leaves
        leave_resp = await ac.delete(
            f"/api/channels/{channel_id}/members/{joiner_user_id}",
            headers={"Authorization": f"Bearer {joiner_token}"},
        )
        assert leave_resp.status_code == 204


async def test_unauthorized_without_token(client):
    resp = await client.get("/api/channels")
    assert resp.status_code == 422  # missing required Authorization header


async def test_private_channel_access_denied(repos):
    """A non-member cannot GET a private channel."""
    user_repo, channel_repo, membership_repo, blacklist = repos
    app = _make_app(user_repo, channel_repo, membership_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "owner", "email": "owner@example.com", "password": "securepass"},
        )
        owner_token = r1.json()["access_token"]

        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "stranger", "email": "stranger@example.com", "password": "securepass"},
        )
        stranger_token = r2.json()["access_token"]

        # Owner creates private channel
        chan = await ac.post(
            "/api/channels",
            json={"name": "priv", "description": "", "channel_type": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        channel_id = chan.json()["id"]

        # Stranger cannot view it
        resp = await ac.get(
            f"/api/channels/{channel_id}",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert resp.status_code == 403


async def test_duplicate_channel_name_returns_409(auth_client):
    client, token = auth_client
    await client.post(
        "/api/channels",
        json={"name": "dup-chan", "description": "", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        "/api/channels",
        json={"name": "dup-chan", "description": "", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_delete_channel_by_creator(auth_client):
    client, token = auth_client
    chan = await client.post(
        "/api/channels",
        json={"name": "todelete", "description": "", "channel_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    channel_id = chan.json()["id"]
    resp = await client.delete(
        f"/api/channels/{channel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_list_members_requires_membership(repos):
    """Non-member gets 403 when listing members of a channel."""
    user_repo, channel_repo, membership_repo, blacklist = repos
    app = _make_app(user_repo, channel_repo, membership_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "mem_owner", "email": "mem_owner@example.com", "password": "securepass"},
        )
        owner_token = r1.json()["access_token"]

        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "mem_out", "email": "mem_out@example.com", "password": "securepass"},
        )
        outsider_token = r2.json()["access_token"]

        chan = await ac.post(
            "/api/channels",
            json={"name": "mem-test", "description": "", "channel_type": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        channel_id = chan.json()["id"]

        resp = await ac.get(
            f"/api/channels/{channel_id}/members",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert resp.status_code == 403
