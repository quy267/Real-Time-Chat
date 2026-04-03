"""UploadFileUseCase — validate and store an uploaded file, return its URL."""

import asyncio

from src.adapters.storage.local_file_storage import LocalFileStorage


class UploadFileUseCase:
    def __init__(self, storage: LocalFileStorage) -> None:
        self._storage = storage

    async def execute(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        user_id: str,  # noqa: ARG002 — reserved for audit logging / ownership
    ) -> str:
        """Validate and save the file; return its public URL path.

        Raises ValidationError if size or content type is invalid.
        File I/O is offloaded to a thread to avoid blocking the async event loop.
        """
        return await asyncio.to_thread(self._storage.save, filename, content, content_type)
