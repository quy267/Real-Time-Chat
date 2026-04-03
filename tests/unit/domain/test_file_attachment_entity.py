"""Unit tests for FileAttachment domain entity."""

import uuid
from datetime import datetime, timezone

from src.domain.entities.file_attachment import FileAttachment


class TestFileAttachmentEntity:
    def test_create_file_attachment_with_all_fields(self):
        file_id = uuid.uuid4()
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        attachment = FileAttachment(
            id=file_id,
            filename="document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            url="https://cdn.example.com/document.pdf",
            user_id=user_id,
            created_at=now,
        )

        assert attachment.id == file_id
        assert attachment.filename == "document.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size_bytes == 1024
        assert attachment.url == "https://cdn.example.com/document.pdf"
        assert attachment.user_id == user_id
        assert attachment.created_at == now

    def test_create_file_attachment_uses_default_created_at(self):
        before = datetime.now(timezone.utc)
        attachment = FileAttachment(
            id=uuid.uuid4(),
            filename="image.png",
            content_type="image/png",
            size_bytes=2048,
            url="https://cdn.example.com/image.png",
            user_id=uuid.uuid4(),
        )
        after = datetime.now(timezone.utc)

        assert before <= attachment.created_at <= after

    def test_file_attachment_is_dataclass(self):
        attachment = FileAttachment(
            id=uuid.uuid4(),
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            url="https://cdn.example.com/test.txt",
            user_id=uuid.uuid4(),
        )
        assert hasattr(attachment, "id")
        assert hasattr(attachment, "filename")
        assert hasattr(attachment, "content_type")
        assert hasattr(attachment, "size_bytes")
        assert hasattr(attachment, "url")
        assert hasattr(attachment, "user_id")
        assert hasattr(attachment, "created_at")

    def test_file_attachment_equality(self):
        file_id = uuid.uuid4()
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        a = FileAttachment(
            id=file_id,
            filename="file.zip",
            content_type="application/zip",
            size_bytes=5000,
            url="https://cdn.example.com/file.zip",
            user_id=user_id,
            created_at=now,
        )
        b = FileAttachment(
            id=file_id,
            filename="file.zip",
            content_type="application/zip",
            size_bytes=5000,
            url="https://cdn.example.com/file.zip",
            user_id=user_id,
            created_at=now,
        )
        assert a == b

    def test_file_attachment_supports_zero_size(self):
        attachment = FileAttachment(
            id=uuid.uuid4(),
            filename="empty.txt",
            content_type="text/plain",
            size_bytes=0,
            url="https://cdn.example.com/empty.txt",
            user_id=uuid.uuid4(),
        )
        assert attachment.size_bytes == 0
