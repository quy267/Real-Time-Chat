"""Integration tests for DM API routes using fake repositories."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_dm_repository import FakeDmRepository
from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, dm_repo, message_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.dm_routes import router as dm_router
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
    from src.use_cases.direct_messages.create_conversation import CreateConversationUseCase
    from src.use_cases.direct_messages.get_dm_history import GetDmHistoryUseCase
    from src.use_cases.direct_messages.list_conversations import ListConversationsUseCase
    from src.use_cases.direct_messages.send_direct_message import SendDirectMessageUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_create_conversation_use_case = lambda: CreateConversationUseCase(dm_repo)
    deps.get_list_conversations_use_case = lambda: ListConversationsUseCase(dm_repo)
    deps.get_send_dm_use_case = lambda: SendDirectMessageUseCase(dm_repo, message_repo)
    deps.get_dm_history_use_case = lambda: GetDmHistoryUseCase(dm_repo, message_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(dm_router)

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
        FakeDmRepository(),
        FakeMessageRepository(),
        FakeTokenBlacklist(),
    )


@pytest.fixture
async def two_users(stores) -> AsyncGenerator[tuple, None]:
    """Yields (client, token_alice, token_bob, dm_repo, message_repo, alice_id, bob_id)."""
    from src.adapters.api.jwt_utils import decode_token

    user_repo, dm_repo, message_repo, blacklist = stores
    app = _make_app(user_repo, dm_repo, message_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_a = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token_alice = reg_a.json()["access_token"]
        alice_id = decode_token(token_alice)["sub"]

        reg_b = await ac.post(
            "/api/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "pass1234"},
        )
        token_bob = reg_b.json()["access_token"]
        bob_id = decode_token(token_bob)["sub"]

        yield ac, token_alice, token_bob, dm_repo, message_repo, alice_id, bob_id


async def test_create_conversation_success(two_users):
    client, token_alice, _, _, _, alice_id, bob_id = two_users

    resp = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "created_at" in data


async def test_create_conversation_idempotent(two_users):
    client, token_alice, _, _, _, alice_id, bob_id = two_users

    r1 = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    r2 = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert r1.json()["id"] == r2.json()["id"]


async def test_self_dm_rejected(two_users):
    client, token_alice, _, _, _, alice_id, _ = two_users

    resp = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": alice_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert resp.status_code == 422


async def test_list_conversations(two_users):
    client, token_alice, _, _, _, alice_id, bob_id = two_users

    await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )

    resp = await client.get(
        "/api/dm/conversations",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


async def test_send_and_get_dm(two_users):
    client, token_alice, _, _, _, alice_id, bob_id = two_users

    create = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    conv_id = create.json()["id"]

    send = await client.post(
        f"/api/dm/conversations/{conv_id}/messages",
        json={"content": "Hello Bob!"},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert send.status_code == 201
    assert send.json()["content"] == "Hello Bob!"
    assert send.json()["conversation_id"] == conv_id


async def test_send_dm_not_participant_returns_403(two_users):
    client, token_alice, _, dm_repo, message_repo, alice_id, bob_id = two_users

    # Create conversation between alice and bob but try with stranger
    create = await client.post(
        "/api/dm/conversations",
        json={"other_user_id": bob_id},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    conv_id = create.json()["id"]

    # Register a third user not in the conversation
    reg_c = await client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "pass1234"},
    )
    token_carol = reg_c.json()["access_token"]

    resp = await client.post(
        f"/api/dm/conversations/{conv_id}/messages",
        json={"content": "intruder"},
        headers={"Authorization": f"Bearer {token_carol}"},
    )
    assert resp.status_code == 403
