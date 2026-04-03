"""Integration tests for thread API routes using fake repositories."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_membership_repository import FakeMembershipRepository
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_thread_repository import FakeThreadRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, message_repo, thread_repo, membership_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.thread_routes import router as thread_router
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
    from src.use_cases.threads.create_thread import CreateThreadUseCase
    from src.use_cases.threads.get_thread_replies import GetThreadRepliesUseCase
    from src.use_cases.threads.reply_to_thread import ReplyToThreadUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_create_thread_use_case = lambda: CreateThreadUseCase(thread_repo, message_repo)
    deps.get_reply_to_thread_use_case = lambda: ReplyToThreadUseCase(
        thread_repo, message_repo, membership_repo
    )
    deps.get_thread_replies_use_case = lambda: GetThreadRepliesUseCase(thread_repo, message_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(thread_router)

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
        FakeMessageRepository(),
        FakeThreadRepository(),
        FakeMembershipRepository(),
        FakeTokenBlacklist(),
    )


@pytest.fixture
async def auth_client(stores) -> AsyncGenerator[tuple, None]:
    """Yields (client, token, message_repo, thread_repo, membership_repo, user_id)."""
    from src.adapters.api.jwt_utils import decode_token

    user_repo, message_repo, thread_repo, membership_repo, blacklist = stores
    app = _make_app(user_repo, message_repo, thread_repo, membership_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]
        user_id = decode_token(token)["sub"]
        yield ac, token, message_repo, thread_repo, membership_repo, user_id


async def test_create_thread_success(auth_client):
    client, token, msg_repo, _, mem_repo, user_id = auth_client
    from src.domain.entities.membership import MemberRole
    from src.domain.entities.message import Message

    channel_id = uuid.uuid4()
    await mem_repo.add_member(uuid.UUID(user_id), channel_id, MemberRole.MEMBER)
    msg = await msg_repo.create(
        Message(id=uuid.uuid4(), content="hi", channel_id=channel_id, user_id=uuid.UUID(user_id))
    )

    resp = await client.post(
        f"/api/messages/{msg.id}/thread",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["parent_message_id"] == str(msg.id)
    assert "id" in data


async def test_create_thread_message_not_found(auth_client):
    client, token, *_ = auth_client
    resp = await client.post(
        f"/api/messages/{uuid.uuid4()}/thread",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_create_thread_duplicate_returns_409(auth_client):
    client, token, msg_repo, _, mem_repo, user_id = auth_client
    from src.domain.entities.membership import MemberRole
    from src.domain.entities.message import Message

    channel_id = uuid.uuid4()
    await mem_repo.add_member(uuid.UUID(user_id), channel_id, MemberRole.MEMBER)
    msg = await msg_repo.create(
        Message(id=uuid.uuid4(), content="hi", channel_id=channel_id, user_id=uuid.UUID(user_id))
    )

    await client.post(
        f"/api/messages/{msg.id}/thread",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        f"/api/messages/{msg.id}/thread",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_reply_to_thread_success(auth_client):
    client, token, msg_repo, thread_repo, mem_repo, user_id = auth_client
    from src.domain.entities.membership import MemberRole
    from src.domain.entities.thread import Thread

    channel_id = uuid.uuid4()
    await mem_repo.add_member(uuid.UUID(user_id), channel_id, MemberRole.MEMBER)
    thread = await thread_repo.create(
        Thread(id=uuid.uuid4(), channel_id=channel_id, parent_message_id=uuid.uuid4())
    )

    resp = await client.post(
        f"/api/threads/{thread.id}/replies",
        json={"content": "my reply"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["content"] == "my reply"


async def test_get_thread_replies_empty(auth_client):
    client, token, _, thread_repo, mem_repo, user_id = auth_client
    from src.domain.entities.thread import Thread

    channel_id = uuid.uuid4()
    thread = await thread_repo.create(
        Thread(id=uuid.uuid4(), channel_id=channel_id, parent_message_id=uuid.uuid4())
    )

    resp = await client.get(
        f"/api/threads/{thread.id}/replies",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []
