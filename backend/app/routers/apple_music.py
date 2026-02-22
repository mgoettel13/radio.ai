"""
FastAPI router for Apple Music API.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas.apple_music import (
    PlaylistResolveRequest,
    PlaylistResolveResponse,
    AppleMusicSettings,
    AppleMusicSettingsUpdate,
)
from app.services.apple_music import get_apple_music_service, AppleMusicService
from app.services.apple_music_token import generate_apple_music_token
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.auth.service import get_current_active_user
from app.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

router = APIRouter(prefix="/api/apple-music", tags=["Apple Music"])


@router.get("/token")
async def get_developer_token():
    """Get the Apple Music developer token for frontend use."""
    try:
        token = generate_apple_music_token()
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resolve-playlist", response_model=PlaylistResolveResponse)
async def resolve_playlist(
    request: PlaylistResolveRequest,
    current_user: User = Depends(get_current_active_user),
    service: AppleMusicService = Depends(get_apple_music_service),
):
    """
    Resolve a playlist of songs to Apple Music IDs.
    Songs not found on Apple Music will be removed from the list.
    """
    # Convert request to list of dicts
    songs = [{"artist": s.artist, "title": s.title} for s in request.songs]
    
    result = await service.resolve_playlist(
        songs=songs,
        skip_not_found=request.skip_not_found
    )
    
    return PlaylistResolveResponse(
        original_count=result["original_count"],
        resolved_count=result["resolved_count"],
        removed_count=result["removed_count"],
        songs=result["songs"],
        removed=result["removed"],
    )


@router.get("/settings", response_model=AppleMusicSettings)
async def get_apple_music_settings(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get Apple Music settings for the current user."""
    try:
        result = await session.execute(
            select(UserPreferences).where(UserPreferences.user_id == current_user.id)
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            return AppleMusicSettings()
        
        return AppleMusicSettings(
            apple_music_connected=bool(prefs.apple_music_connected) if prefs.apple_music_connected else False,
            apple_music_subscription_type=prefs.apple_music_subscription_type,
            apple_music_authorized_at=prefs.apple_music_authorized_at,
            apple_music_storefront=prefs.apple_music_storefront,
        )
    except Exception as e:
        print(f"Error loading Apple Music settings: {e}")
        raise


@router.put("/settings", response_model=AppleMusicSettings)
async def update_apple_music_settings(
    settings: AppleMusicSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update Apple Music subscription settings."""
    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        # Create new preferences
        prefs = UserPreferences(user_id=current_user.id)
        session.add(prefs)
    
    prefs.apple_music_connected = settings.apple_music_connected
    prefs.apple_music_subscription_type = settings.apple_music_subscription_type
    prefs.apple_music_storefront = settings.apple_music_storefront
    
    if settings.apple_music_connected:
        prefs.apple_music_authorized_at = datetime.utcnow()
    else:
        prefs.apple_music_authorized_at = None
    
    await session.commit()
    await session.refresh(prefs)
    
    return AppleMusicSettings(
        apple_music_connected=prefs.apple_music_connected or False,
        apple_music_subscription_type=prefs.apple_music_subscription_type,
        apple_music_authorized_at=prefs.apple_music_authorized_at,
        apple_music_storefront=prefs.apple_music_storefront,
    )
