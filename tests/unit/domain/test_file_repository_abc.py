"""Unit tests for FileRepository abstract base class — verifies interface contract."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.entities.file_attachment import FileAttachment
from src.domain.repositories.file_repository import FileRepository


class ConcreteFileRepository(FileRepository):
    """Minimal in-memory implementation to exercise the ABC."""

    def __init__(self):
        self._store: dict[uuid.UUID, FileAttachment] = {}

    async def save(self, attachment: FileAttachment) -> FileAttachment:
        self._store[attachment.id] = attachment
        return attachment

    async def get_by_id(self, file_id: uuid.UUID) -> FileAttachment | None:
        return self._store.get(file_id)

    async def delete(self, file_id: uuid.UUID) -> None:
        self._store.pop(file_id, None)


def _make_attachment() -> FileAttachment:
    return FileAttachment(
        id=uuid.uuid4(),
        filename="test.png",
        content_type="image/png",
        size_bytes=512,
        url="https://cdn.example.com/test.png",
        user_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def repo():
    return ConcreteFileRepository()


class TestFileRepositoryABC:
    def test_cannot_instantiate_abstract_class_directly(self):
        with pytest.raises(TypeError):
            FileRepository()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repo):
        attachment = _make_attachment()
        saved = await repo.save(attachment)
        assert saved.id == attachment.id
        fetched = await repo.get_by_id(attachment.id)
        assert fetched is not None
        assert fetched.id == attachment.id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self, repo):
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_attachment(self, repo):
        attachment = _make_attachment()
        await repo.save(attachment)
        await repo.delete(attachment.id)
        result = await repo.get_by_id(attachment.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_does_not_raise(self, repo):
        await repo.delete(uuid.uuid4())  # should not raise
