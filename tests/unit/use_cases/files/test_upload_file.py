"""Unit tests for UploadFileUseCase and LocalFileStorage."""

import uuid

import pytest

from src.adapters.storage.local_file_storage import LocalFileStorage
from src.domain.exceptions import ValidationError
from src.use_cases.files.upload_file import UploadFileUseCase

_10MB = 10 * 1024 * 1024


@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(upload_dir=str(tmp_path), max_size_bytes=_10MB)


@pytest.fixture
def uc(storage):
    return UploadFileUseCase(storage)


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


# --- LocalFileStorage validation ---

def test_storage_rejects_oversized_file(storage):
    content = b"x" * (_10MB + 1)
    with pytest.raises(ValidationError, match="10MB"):
        storage.validate("file.txt", content, "text/plain")


def test_storage_rejects_disallowed_content_type(storage):
    with pytest.raises(ValidationError, match="not allowed"):
        storage.validate("file.exe", b"data", "application/x-msdownload")


def test_storage_rejects_path_traversal_filename(storage):
    with pytest.raises(ValidationError, match="Invalid filename"):
        storage.validate("../../etc/passwd", b"data", "text/plain")


def test_storage_saves_file_and_returns_url(storage, tmp_path):
    content = b"hello world"
    url = storage.save("test.txt", content, "text/plain")

    assert url.startswith("/uploads/")
    stored_name = url.removeprefix("/uploads/")
    assert (tmp_path / stored_name).exists()
    assert (tmp_path / stored_name).read_bytes() == content


def test_storage_delete_removes_file(storage, tmp_path):
    content = b"delete me"
    url = storage.save("del.txt", content, "text/plain")
    stored_name = url.removeprefix("/uploads/")
    assert (tmp_path / stored_name).exists()

    storage.delete(url)
    assert not (tmp_path / stored_name).exists()


def test_storage_delete_nonexistent_is_noop(storage):
    storage.delete("/uploads/does_not_exist.txt")  # must not raise


# --- UploadFileUseCase ---

async def test_upload_file_success(uc, user_id, tmp_path):
    url = await uc.execute(
        filename="photo.png",
        content=b"fake-png-bytes",
        content_type="image/png",
        user_id=user_id,
    )
    assert url.startswith("/uploads/")
    stored_name = url.removeprefix("/uploads/")
    assert (tmp_path / stored_name).exists()


async def test_upload_file_too_large(uc, user_id):
    with pytest.raises(ValidationError, match="10MB"):
        await uc.execute(
            filename="big.png",
            content=b"x" * (_10MB + 1),
            content_type="image/png",
            user_id=user_id,
        )


async def test_upload_file_disallowed_type(uc, user_id):
    with pytest.raises(ValidationError, match="not allowed"):
        await uc.execute(
            filename="virus.exe",
            content=b"MZ\x90",
            content_type="application/x-msdownload",
            user_id=user_id,
        )


async def test_upload_allowed_types(uc, user_id):
    for ct, fname, data in [
        ("image/jpeg", "photo.jpg", b"jpeg"),
        ("application/pdf", "doc.pdf", b"pdf"),
        ("text/plain", "readme.txt", b"text"),
        ("text/csv", "data.csv", b"csv"),
    ]:
        url = await uc.execute(filename=fname, content=data, content_type=ct, user_id=user_id)
        assert url.startswith("/uploads/")
