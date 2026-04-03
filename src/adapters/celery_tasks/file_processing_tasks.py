"""Celery tasks for file processing — thumbnail generation for uploaded images."""

import logging
from pathlib import Path

from src.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (200, 200)
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@celery_app.task(name="file_processing_tasks.generate_thumbnail", bind=True, max_retries=3)
def generate_thumbnail(self, file_path: str) -> dict:
    """Generate a 200x200 thumbnail for an uploaded image file.

    Args:
        file_path: Absolute path to the source image file.

    Returns:
        Dict with thumbnail_path on success, or error details on failure.
    """
    path = Path(file_path)

    if not path.exists():
        logger.warning("generate_thumbnail: file not found at %s", file_path)
        return {"status": "skipped", "reason": "file_not_found", "path": file_path}

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        logger.info("generate_thumbnail: unsupported format %s, skipping", path.suffix)
        return {"status": "skipped", "reason": "unsupported_format", "path": file_path}

    try:
        from PIL import Image

        with Image.open(path) as img:
            img.thumbnail(THUMBNAIL_SIZE)
            thumb_path = path.with_name(f"{path.stem}_thumb{path.suffix}")
            img.save(thumb_path)
            logger.info("Thumbnail saved to %s", thumb_path)
            return {"status": "ok", "thumbnail_path": str(thumb_path)}

    except Exception as exc:
        logger.error("generate_thumbnail failed for %s: %s", file_path, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
