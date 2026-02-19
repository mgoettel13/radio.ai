"""
Pydantic schemas for station endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StationCreate(BaseModel):
    """Schema for creating a new station."""
    name: str = Field(..., min_length=1, max_length=255, description="Station name")
    description: Optional[str] = Field(None, description="Music description")
    example_songs: Optional[list[str]] = Field(
        default_factory=list, 
        description="List of example songs (3-5 recommended)"
    )
    duration: int = Field(default=1, ge=1, le=24, description="Playlist duration in hours (1-24)")
    image_url: Optional[str] = Field(None, max_length=50000, description="Station image URL")


class StationUpdate(BaseModel):
    """Schema for updating an existing station."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    example_songs: Optional[list[str]] = None
    duration: Optional[int] = Field(None, ge=1, le=24)
    image_url: Optional[str] = Field(None, max_length=50000)


class StationRead(BaseModel):
    """Schema for reading station data."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    example_songs: list[str] = []
    duration: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationList(BaseModel):
    """Schema for listing multiple stations."""
    stations: list[StationRead]
    total: int
