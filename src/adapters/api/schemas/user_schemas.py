"""Pydantic schemas for user profile API requests and responses."""

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    avatar_url: str | None
    status: str
    created_at: str


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, max_length=64)
    avatar_url: str | None = None
    status: str | None = None
