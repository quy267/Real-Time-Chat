"""Pydantic request/response schemas for channel and membership endpoints."""

from typing import Any

from pydantic import BaseModel


class CreateChannelRequest(BaseModel):
    name: str
    description: str = ""
    channel_type: str = "public"


class UpdateChannelRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class ChannelResponse(BaseModel):
    id: str
    name: str
    description: str | None
    channel_type: str
    creator_id: str
    created_at: str
    updated_at: str


class MemberResponse(BaseModel):
    user_id: str
    channel_id: str
    role: str
    joined_at: str


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int
