"""Integration tests for reaction API routes using fake repositories."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_message_repository import FakeMessageRepository
from tests.fakes.fake_reaction_repository import FakeReactionRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, message_repo, reaction_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.reaction_routes import router as reaction_router
    from src.domain.exceptions import (
        AuthenticationError,
        DuplicateEntityError,
        EntityNotFoundError,
        ValidationError,
    )
    from src.use_cases.auth.login_user import LoginUserUseCase
    from src.use_cases.auth.logout_user import LogoutUserUseCase
    from src.use_cases.auth.refresh_token import RefreshTokenUseCase
    from src.use_cases.auth.register_user import RegisterUserUseCase
    from src.use_cases.reactions.add_reaction import AddReactionUseCase
    from src.use_cases.reactions.list_reactions import ListReactionsUseCase
    from src.use_cases.reactions.remove_reaction import RemoveReactionUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_add_reaction_use_case = lambda: AddReactionUseCase(reaction_repo, message_repo)
    deps.get_remove_reaction_use_case = lambda: RemoveReactionUseCase(reaction_repo)
    deps.get_list_reactions_use_case = lambda: ListReactionsUseCase(reaction_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(reaction_router)

    @app.exception_handler(DuplicateEntityError)
    async def dup_handler(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def val_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(EntityNotFoundError)
    async def nf_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    return app


@pytest.fixture
def stores():
    return (
        FakeUserRepository(),
        FakeMessageRepository(),
        FakeReactionRepository(),
        FakeTokenBlacklist(),
    )


@pytest.fixture
async def auth_client(stores) -> AsyncGenerator[tuple[AsyncClient, str, str], None]:
    """Yields (client, token, message_id) — user registered, message seeded."""
    user_repo, message_repo, reaction_repo, blacklist = stores
    app = _make_app(user_repo, message_repo, reaction_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]

        # Seed a message directly via repo
        from src.adapters.api.jwt_utils import decode_token
        from src.domain.entities.message import Message

        payload = decode_token(token)
        user_id = payload["sub"]
        msg = Message(
            id=uuid.uuid4(),
            content="test message",
            channel_id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
        )
        await message_repo.create(msg)
        yield ac, token, str(msg.id)


async def test_add_reaction_success(auth_client):
    client, token, message_id = auth_client
    resp = await client.post(
        f"/api/messages/{message_id}/reactions",
        json={"emoji": "👍"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["emoji"] == "👍"
    assert data["message_id"] == message_id


async def test_add_reaction_message_not_found(auth_client):
    client, token, _ = auth_client
    resp = await client.post(
        f"/api/messages/{uuid.uuid4()}/reactions",
        json={"emoji": "👍"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_add_reaction_duplicate_returns_409(auth_client):
    client, token, message_id = auth_client
    await client.post(
        f"/api/messages/{message_id}/reactions",
        json={"emoji": "👍"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        f"/api/messages/{message_id}/reactions",
        json={"emoji": "👍"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_list_reactions_empty(auth_client):
    client, token, message_id = auth_client
    resp = await client.get(
        f"/api/messages/{message_id}/reactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reactions"] == []
    assert data["total"] == 0


async def test_list_reactions_after_adding(auth_client):
    client, token, message_id = auth_client
    await client.post(
        f"/api/messages/{message_id}/reactions",
        json={"emoji": "❤️"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/messages/{message_id}/reactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["reactions"][0]["emoji"] == "❤️"


async def test_remove_reaction_success(auth_client):
    client, token, message_id = auth_client
    await client.post(
        f"/api/messages/{message_id}/reactions",
        json={"emoji": "👍"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.delete(
        f"/api/messages/{message_id}/reactions/👍",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_remove_reaction_not_found_returns_404(auth_client):
    client, token, message_id = auth_client
    resp = await client.delete(
        f"/api/messages/{message_id}/reactions/👍",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_reaction_requires_auth(stores):
    user_repo, message_repo, reaction_repo, blacklist = stores
    app = _make_app(user_repo, message_repo, reaction_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/messages/{uuid.uuid4()}/reactions")
        assert resp.status_code == 422  # missing auth header
