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
    # News configuration
    play_news: bool = Field(default=False, description="Enable news playback")
    play_news_at_start: bool = Field(default=False, description="Play news at stream start")
    news_interval_minutes: Optional[int] = Field(None, ge=15, le=60, description="News interval in minutes (15, 30, or 60)")


class StationUpdate(BaseModel):
    """Schema for updating an existing station."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    example_songs: Optional[list[str]] = None
    duration: Optional[int] = Field(None, ge=1, le=24)
    image_url: Optional[str] = Field(None, max_length=50000)
    # News configuration
    play_news: Optional[bool] = Field(None, description="Enable news playback")
    play_news_at_start: Optional[bool] = Field(None, description="Play news at stream start")
    news_interval_minutes: Optional[int] = Field(None, ge=15, le=60, description="News interval in minutes (15, 30, or 60)")


class StationRead(BaseModel):
    """Schema for reading station data."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    example_songs: list[str] = []
    duration: int
    image_url: Optional[str] = None
    # News configuration
    play_news: bool = False
    play_news_at_start: bool = False
    news_interval_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationList(BaseModel):
    """Schema for listing multiple stations."""
    stations: list[StationRead]
    total: int


class StationNewsResponse(BaseModel):
    """Schema for station news generation response."""
    radio_script: str = Field(..., description="The generated radio news script")
    audio_url: str = Field(..., description="URL of the generated TTS audio")
    duration_seconds: int = Field(..., description="Duration of the audio in seconds")
    generated_at: datetime = Field(..., description="Timestamp when news was generated")
