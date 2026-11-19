from datetime import datetime

from pydantic import BaseModel, Field


class ImageRead(BaseModel):
    """Response body for an image's metadata."""

    id: int
    title: str
    description: str | None
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    url: str


class ImageUpdate(BaseModel):
    """Request body for PATCH /images/{id}. Only sent fields are changed."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
