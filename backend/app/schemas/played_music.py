"""
Pydantic schemas for PlayedMusic API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class PlayedMusicBase(BaseModel):
    """Base schema for played music."""
    song_id: str = Field(..., description="Apple Music song ID")
    artist: str = Field(..., description="Artist name")
    title: str = Field(..., description="Song title")
    station_id: Optional[uuid.UUID] = Field(None, description="Station ID if applicable")


class PlayedMusicCreate(PlayedMusicBase):
    """Schema for creating a played music record."""
    pass


class PlayedMusicResponse(PlayedMusicBase):
    """Schema for played music response."""
    id: uuid.UUID
    user_id: uuid.UUID
    play_date: datetime
    play_count: int
    
    class Config:
        from_attributes = True


class PlayedMusicUpdate(BaseModel):
    """Schema for updating a played music record."""
    play_count: Optional[int] = Field(None, ge=1)


class PlayedMusicListResponse(BaseModel):
    """Schema for list of played music."""
    songs: List[PlayedMusicResponse]
    total: int
