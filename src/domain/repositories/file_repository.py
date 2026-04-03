"""Abstract FileRepository — async interface for file attachment persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.file_attachment import FileAttachment


class FileRepository(ABC):
    @abstractmethod
    async def save(self, attachment: FileAttachment) -> FileAttachment:
        """Persist file attachment metadata and return it."""

    @abstractmethod
    async def get_by_id(self, file_id: UUID) -> FileAttachment | None:
        """Return file attachment by primary key, or None if not found."""

    @abstractmethod
    async def delete(self, file_id: UUID) -> None:
        """Remove file attachment metadata by primary key."""
