"""Pydantic schemas for search API requests and responses."""

from pydantic import BaseModel


class MessageSearchResponse(BaseModel):
    id: str
    content: str
    channel_id: str
    user_id: str
    created_at: str


class ChannelSearchResponse(BaseModel):
    id: str
    name: str
    description: str | None
    channel_type: str


class SearchMessagesResult(BaseModel):
    query: str
    items: list[MessageSearchResponse]
    total: int


class SearchChannelsResult(BaseModel):
    query: str
    items: list[ChannelSearchResponse]
    total: int
