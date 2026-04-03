"""Integration tests for message REST API routes using fake repositories."""

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
    """Build FastAPI app wired entirely to in-memory fakes."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.channel_routes import router as channel_router
    from src.adapters.api.routes.message_routes import router as message_router
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
    from src.use_cases.messaging.delete_message import DeleteMessageUseCase
    from src.use_cases.messaging.edit_message import EditMessageUseCase
    from src.use_cases.messaging.get_message_history import GetMessageHistoryUseCase
    from src.use_cases.messaging.send_message import SendMessageUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_create_channel_use_case = lambda: CreateChannelUseCase(channel_repo, membership_repo)
    deps.get_list_channels_use_case = lambda: ListChannelsUseCase(channel_repo)
    deps.get_get_channel_use_case = lambda: GetChannelUseCase(channel_repo, membership_repo)
    deps.get_update_channel_use_case = lambda: UpdateChannelUseCase(channel_repo, membership_repo)
    deps.get_delete_channel_use_case = lambda: DeleteChannelUseCase(channel_repo, membership_repo)
    deps.get_join_channel_use_case = lambda: JoinChannelUseCase(channel_repo, membership_repo)
    deps.get_leave_channel_use_case = lambda: LeaveChannelUseCase(channel_repo, membership_repo)
    deps.get_list_members_use_case = lambda: ListMembersUseCase(channel_repo, membership_repo)
    deps.get_send_message_use_case = lambda: SendMessageUseCase(message_repo, membership_repo)
    deps.get_edit_message_use_case = lambda: EditMessageUseCase(message_repo)
    deps.get_delete_message_use_case = lambda: DeleteMessageUseCase(message_repo)
    deps.get_get_message_history_use_case = lambda: GetMessageHistoryUseCase(message_repo, membership_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(channel_router)
    app.include_router(message_router)

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
async def auth_client(stores) -> AsyncGenerator[tuple[AsyncClient, str, str], None]:
    """Yields (client, token, channel_id) — user registered and joined a channel."""
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
            json={"name": "general", "description": "", "channel_type": "public"},
            headers={"Authorization": f"Bearer {token}"},
        )
        channel_id = chan.json()["id"]
        yield ac, token, channel_id


async def test_get_message_history_empty(auth_client):
    client, token, channel_id = auth_client
    resp = await client.get(
        f"/api/channels/{channel_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


async def test_get_message_history_non_member_returns_403(stores):
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
            f"/api/channels/{channel_id}/messages",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert resp.status_code == 403


async def test_edit_message_success(auth_client):
    client, token, channel_id = auth_client

    # Send a message via the use case directly through DI
    import src.adapters.api.dependencies as deps
    uc = deps.get_send_message_use_case()
    # Extract user_id from token
    from src.adapters.api.jwt_utils import decode_token
    payload = decode_token(token)
    user_id = payload["sub"]

    msg = await uc.execute(content="original", channel_id=channel_id, user_id=user_id)

    resp = await client.put(
        f"/api/messages/{msg.id}",
        json={"content": "edited content"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "edited content"


async def test_edit_message_not_found_returns_404(auth_client):
    client, token, _ = auth_client
    resp = await client.put(
        f"/api/messages/{uuid.uuid4()}",
        json={"content": "edited"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_edit_not_author_returns_403(stores):
    user_repo, channel_repo, membership_repo, message_repo, blacklist = stores
    app = _make_app(user_repo, channel_repo, membership_repo, message_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "author", "email": "author@example.com", "password": "pass1234"},
        )
        author_token = r1.json()["access_token"]

        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "other", "email": "other@example.com", "password": "pass1234"},
        )
        other_token = r2.json()["access_token"]

        chan = await ac.post(
            "/api/channels",
            json={"name": "edit-test", "description": "", "channel_type": "public"},
            headers={"Authorization": f"Bearer {author_token}"},
        )
        channel_id = chan.json()["id"]

        # Author sends message
        import src.adapters.api.dependencies as deps
        from src.adapters.api.jwt_utils import decode_token
        payload = decode_token(author_token)
        author_id = payload["sub"]
        msg = await deps.get_send_message_use_case().execute(
            content="my message", channel_id=channel_id, user_id=author_id
        )

        # Other user tries to edit
        resp = await ac.put(
            f"/api/messages/{msg.id}",
            json={"content": "hacked"},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403


async def test_delete_message_success(auth_client):
    client, token, channel_id = auth_client

    import src.adapters.api.dependencies as deps
    from src.adapters.api.jwt_utils import decode_token
    payload = decode_token(token)
    user_id = payload["sub"]

    msg = await deps.get_send_message_use_case().execute(
        content="to delete", channel_id=channel_id, user_id=user_id
    )

    resp = await client.delete(
        f"/api/messages/{msg.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_message_not_found_returns_404(auth_client):
    client, token, _ = auth_client
    resp = await client.delete(
        f"/api/messages/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
