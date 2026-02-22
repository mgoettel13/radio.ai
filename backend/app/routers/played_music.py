"""
FastAPI router for PlayedMusic API.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import uuid

from app.schemas.played_music import (
    PlayedMusicCreate,
    PlayedMusicResponse,
    PlayedMusicListResponse,
)
from app.services.played_music import PlayedMusicService
from app.models.user import User
from app.auth.service import get_current_active_user
from app.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/played-music", tags=["Played Music"])


@router.post("", response_model=PlayedMusicResponse)
async def record_play(
    play_data: PlayedMusicCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Record a song play. Increments play_count if already played.
    """
    service = PlayedMusicService(session)
    played = await service.record_play(
        user_id=current_user.id,
        song_id=play_data.song_id,
        artist=play_data.artist,
        title=play_data.title,
        station_id=play_data.station_id
    )
    return played


@router.get("", response_model=PlayedMusicListResponse)
async def get_my_plays(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all songs played by the current user.
    """
    service = PlayedMusicService(session)
    songs, total = await service.get_user_plays(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return PlayedMusicListResponse(songs=songs, total=total)


@router.get("/most-played", response_model=list[PlayedMusicResponse])
async def get_most_played(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get most played songs for the current user.
    """
    service = PlayedMusicService(session)
    songs = await service.get_most_played(
        user_id=current_user.id,
        limit=limit
    )
    return songs


@router.get("/station/{station_id}", response_model=list[PlayedMusicResponse])
async def get_station_plays(
    station_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get play history for a specific station.
    """
    service = PlayedMusicService(session)
    songs = await service.get_station_plays(
        station_id=station_id,
        limit=limit
    )
    return songs


@router.delete("/{play_id}")
async def delete_play(
    play_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete a play record.
    """
    service = PlayedMusicService(session)
    deleted = await service.delete_play(
        user_id=current_user.id,
        play_id=play_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Play record not found")
    return {"message": "Play record deleted"}
