from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from src.infrastructure.config import settings
from src.infrastructure.logging_config import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging("DEBUG" if settings.debug else "INFO")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- Domain exception handlers ---
    @app.exception_handler(DuplicateEntityError)
    async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    # --- Routes ---
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.channel_routes import router as channel_router
    from src.adapters.api.routes.dm_routes import router as dm_router
    from src.adapters.api.routes.file_routes import router as file_router
    from src.adapters.api.routes.mention_routes import router as mention_router
    from src.adapters.api.routes.message_routes import router as message_router
    from src.adapters.api.routes.notification_routes import router as notification_router
    from src.adapters.api.routes.reaction_routes import router as reaction_router
    from src.adapters.api.routes.search_routes import router as search_router
    from src.adapters.api.routes.thread_routes import router as thread_router
    from src.adapters.api.routes.user_routes import router as user_router

    app.include_router(auth_router)
    app.include_router(channel_router)
    app.include_router(message_router)
    app.include_router(thread_router)
    app.include_router(dm_router)
    app.include_router(mention_router)
    app.include_router(search_router)
    app.include_router(reaction_router)
    app.include_router(file_router)
    app.include_router(user_router)
    app.include_router(notification_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return app


def create_socket_app():
    """Create Socket.IO ASGI app wrapping FastAPI. Import event handlers to register them."""
    # Importing registers all @sio.event handlers with the sio instance
    import src.adapters.websocket.event_handlers.chat_events  # noqa: F401
    import src.adapters.websocket.event_handlers.presence_events  # noqa: F401
    import src.adapters.websocket.event_handlers.typing_events  # noqa: F401
    from src.adapters.websocket.socket_server import create_socket_app as _wrap

    fastapi_app = create_app()
    return _wrap(fastapi_app)


# Top-level ASGI app: Socket.IO wrapping FastAPI
# Used by uvicorn / gunicorn in production: `uvicorn src.main:app`
app = create_socket_app()
