"""Integration tests for notification API routes using fake repositories."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.notification import Notification
from tests.fakes.fake_notification_repository import FakeNotificationRepository
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, notif_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.notification_routes import router as notif_router
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
    from src.use_cases.notifications.list_notifications import ListNotificationsUseCase
    from src.use_cases.notifications.mark_all_read import MarkAllReadUseCase
    from src.use_cases.notifications.mark_notification_read import MarkNotificationReadUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_list_notifications_use_case = lambda: ListNotificationsUseCase(notif_repo)
    deps.get_mark_notification_read_use_case = lambda: MarkNotificationReadUseCase(notif_repo)
    deps.get_mark_all_read_use_case = lambda: MarkAllReadUseCase(notif_repo)
    deps.get_notification_repo = lambda: notif_repo

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(notif_router)

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


def _make_notification(user_id: uuid.UUID, read: bool = False) -> Notification:
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type="mention",
        title="You were mentioned",
        content="alice mentioned you",
        reference_id=str(uuid.uuid4()),
        read=read,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def stores():
    return FakeUserRepository(), FakeNotificationRepository(), FakeTokenBlacklist()


@pytest.fixture
async def authenticated_client(stores):
    """Yields (client, token, user_id, notif_repo)."""
    from src.adapters.api.jwt_utils import decode_token

    user_repo, notif_repo, blacklist = stores
    app = _make_app(user_repo, notif_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]
        user_id = decode_token(token)["sub"]
        yield ac, token, user_id, notif_repo


async def test_list_notifications_empty(authenticated_client):
    client, token, user_id, _ = authenticated_client

    resp = await client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["limit"] == 50
    assert data["offset"] == 0


async def test_list_notifications_returns_user_notifications(authenticated_client):
    client, token, user_id, notif_repo = authenticated_client

    await notif_repo.create(_make_notification(uuid.UUID(user_id)))
    await notif_repo.create(_make_notification(uuid.UUID(user_id)))

    resp = await client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 2


async def test_list_notifications_unread_only_filter(authenticated_client):
    client, token, user_id, notif_repo = authenticated_client

    await notif_repo.create(_make_notification(uuid.UUID(user_id), read=True))
    await notif_repo.create(_make_notification(uuid.UUID(user_id), read=False))

    resp = await client.get(
        "/api/notifications?unread_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["read"] is False


async def test_count_unread_notifications(authenticated_client):
    client, token, user_id, notif_repo = authenticated_client

    await notif_repo.create(_make_notification(uuid.UUID(user_id), read=False))
    await notif_repo.create(_make_notification(uuid.UUID(user_id), read=False))
    await notif_repo.create(_make_notification(uuid.UUID(user_id), read=True))

    resp = await client.get(
        "/api/notifications/count",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["count"] == 2


async def test_mark_notification_read(authenticated_client):
    client, token, user_id, notif_repo = authenticated_client

    notif = await notif_repo.create(_make_notification(uuid.UUID(user_id)))

    resp = await client.put(
        f"/api/notifications/{notif.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    updated = await notif_repo.get_by_id(notif.id)
    assert updated.read is True


async def test_mark_notification_read_not_found(authenticated_client):
    client, token, _, _ = authenticated_client

    resp = await client.put(
        f"/api/notifications/{uuid.uuid4()}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404


async def test_mark_notification_read_wrong_owner(authenticated_client, stores):
    client, token, user_id, notif_repo = authenticated_client

    # Create notification for another user
    other_id = uuid.uuid4()
    notif = await notif_repo.create(_make_notification(other_id))

    resp = await client.put(
        f"/api/notifications/{notif.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


async def test_mark_all_read(authenticated_client):
    client, token, user_id, notif_repo = authenticated_client

    for _ in range(3):
        await notif_repo.create(_make_notification(uuid.UUID(user_id)))

    resp = await client.put(
        "/api/notifications/read-all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    count = await notif_repo.count_unread(uuid.UUID(user_id))
    assert count == 0


async def test_list_notifications_requires_auth(stores):
    """Unauthenticated request is rejected — FastAPI returns 422 for missing required header."""
    user_repo, notif_repo, blacklist = stores
    app = _make_app(user_repo, notif_repo, blacklist)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # No Authorization header → FastAPI Header(...) validation fails with 422
        resp_no_header = await ac.get("/api/notifications")
        # Invalid token → middleware returns 401
        resp_bad_token = await ac.get(
            "/api/notifications",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

    assert resp_no_header.status_code == 422
    assert resp_bad_token.status_code == 401
