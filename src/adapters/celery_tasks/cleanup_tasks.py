"""Celery periodic tasks for cleaning up expired data and stale records."""

import logging

from src.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_tasks.clean_expired_data")
def clean_expired_data() -> dict:
    """Placeholder cleanup task — scans and removes stale Redis keys and expired data.

    Runs periodically via Celery beat. Idempotent and safe to retry.
    """
    logger.info("Starting expired data cleanup")

    actions = []

    # Clean stale presence keys (users offline > 5 minutes)
    logger.info("Would scan Redis for stale presence:* keys older than 5 minutes")
    actions.append("stale_presence_keys_checked")

    # Clean blacklisted tokens that have expired naturally
    logger.info("Would scan Redis for expired blacklist:* token entries")
    actions.append("expired_token_blacklist_checked")

    # Archive messages older than configurable threshold (placeholder)
    logger.info("Would archive messages older than retention threshold")
    actions.append("message_archival_checked")

    logger.info("Expired data cleanup complete: %s", actions)
    return {"actions": actions, "status": "ok"}
