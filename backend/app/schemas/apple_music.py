"""
Pydantic schemas for Apple Music API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SongInput(BaseModel):
    """Input schema for a song to be resolved."""
    artist: str = Field(..., description="Artist name")
    title: str = Field(..., description="Song title")


class PlaylistResolveRequest(BaseModel):
    """Request schema for resolving a playlist."""
    songs: List[SongInput] = Field(..., description="List of songs to resolve")
    skip_not_found: bool = Field(
        default=True, 
        description="If True, remove songs not found from result"
    )


class ResolvedSong(BaseModel):
    """Schema for a resolved song with Apple Music ID."""
    artist: str
    title: str
    apple_music_id: str
    name: Optional[str] = None
    duration_ms: Optional[int] = None
    artwork: Optional[Dict[str, Any]] = None
    playback_url: Optional[str] = None
    album_name: Optional[str] = None
    genre: Optional[str] = None


class RemovedSong(BaseModel):
    """Schema for a song that couldn't be found."""
    artist: str
    title: str


class PlaylistResolveResponse(BaseModel):
    """Response schema for playlist resolution."""
    original_count: int
    resolved_count: int
    removed_count: int
    songs: List[ResolvedSong]
    removed: List[RemovedSong]


class AppleMusicSettings(BaseModel):
    """Schema for Apple Music user settings."""
    apple_music_connected: bool = False
    apple_music_subscription_type: Optional[str] = None
    apple_music_authorized_at: Optional[datetime] = None
    apple_music_storefront: Optional[str] = None


class AppleMusicSettingsUpdate(BaseModel):
    """Schema for updating Apple Music settings."""
    apple_music_connected: bool
    apple_music_subscription_type: Optional[str] = None
    apple_music_storefront: Optional[str] = None
