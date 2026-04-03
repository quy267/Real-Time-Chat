"""Pydantic schemas for file upload API responses."""

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    url: str
    filename: str
    content_type: str
    size_bytes: int
