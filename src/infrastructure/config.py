from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Real-Time Chat"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://chat:chat@db:5432/chat"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Celery
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # File uploads
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10

    # CORS
    cors_origins: str = "*"

    model_config = {"env_prefix": "CHAT_", "env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        import os

        # Only enforce in production: when CHAT_DEBUG is explicitly set to false
        # (not just the default). This prevents blocking test runs.
        debug_env = os.environ.get("CHAT_DEBUG", "").lower()
        explicitly_production = debug_env in ("false", "0", "no")
        if explicitly_production and self.jwt_secret == "change-me-in-production":
            raise ValueError("CHAT_JWT_SECRET must be set in production (CHAT_DEBUG=false)")
        return self


settings = Settings()
