"""LocalFileStorage — saves uploaded files to local disk, returns URL path."""

import hashlib
import os
import re
import time
from pathlib import Path

from src.domain.exceptions import ValidationError

# Allowed MIME type prefixes and exact types
_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
        "text/markdown",
    ]
)

_SAFE_FILENAME_RE = re.compile(r"[^\w.\-]")


class LocalFileStorage:
    """Stores files on local disk under a configurable directory.

    URL paths are returned as ``/uploads/<filename>`` — the web server
    or FastAPI static-file mount is responsible for serving them.
    """

    def __init__(self, upload_dir: str, max_size_bytes: int) -> None:
        self._upload_dir = Path(upload_dir)
        self._max_size_bytes = max_size_bytes
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, filename: str, content_bytes: bytes, content_type: str) -> None:
        """Validate size and content type before saving.

        Raises ValidationError on failure.
        """
        if len(content_bytes) > self._max_size_bytes:
            mb = self._max_size_bytes // (1024 * 1024)
            raise ValidationError(f"File exceeds maximum size of {mb}MB.")

        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                f"Content type '{content_type}' is not allowed."
            )

        # Guard against path traversal in the filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationError("Invalid filename.")

    def save(self, filename: str, content_bytes: bytes, content_type: str) -> str:
        """Validate, persist to disk, and return the public URL path.

        The stored filename is prefixed with a timestamp+hash to ensure
        uniqueness and avoid collisions.
        """
        self.validate(filename, content_bytes, content_type)

        safe_name = _SAFE_FILENAME_RE.sub("_", filename)
        prefix = f"{int(time.time())}_{hashlib.sha1(content_bytes[:256]).hexdigest()[:8]}"
        stored_name = f"{prefix}_{safe_name}"

        dest = self._upload_dir / stored_name
        dest.write_bytes(content_bytes)

        return f"/uploads/{stored_name}"

    def delete(self, file_path: str) -> None:
        """Delete file at the given URL path (e.g. /uploads/foo.png).

        No-op if file does not exist.
        """
        stored_name = os.path.basename(file_path)
        dest = self._upload_dir / stored_name
        try:
            dest.unlink()
        except FileNotFoundError:
            pass
