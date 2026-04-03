from celery import Celery

from src.infrastructure.config import settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    app = Celery(
        "realtime_chat",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
    app.autodiscover_tasks(["src.adapters.celery_tasks"])
    return app


celery_app = create_celery_app()
