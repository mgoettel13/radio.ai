"""
Pydantic schemas for playlist generation endpoints.
"""

from typing import Optional, List

from pydantic import BaseModel, Field


class PlaylistSong(BaseModel):
    """Schema for a single song in the playlist."""
    artist: str = Field(..., description="Artist name")
    title: str = Field(..., description="Song title")
    year: Optional[int] = Field(None, description="Release year")
    genre: str = Field(..., description="Music genre")
    why_this_song: str = Field(..., description="Explanation of why this song fits the station")


class PlaylistResponse(BaseModel):
    """Schema for playlist generation response."""
    station_name: str = Field(..., description="Name of the radio station")
    station_id: Optional[str] = Field(None, description="ID of the radio station")
    total_duration_hours: int = Field(..., description="Duration of playlist in hours")
    songs: List[PlaylistSong] = Field(..., description="List of songs in the playlist")

    class Config:
        from_attributes = True
