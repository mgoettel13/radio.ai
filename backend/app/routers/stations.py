"""
Station router for managing user radio stations.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_active_user
from app.database import get_async_session
from app.models.station import Station
from app.models.user import User
from app.schemas.station import (
    StationCreate,
    StationRead,
    StationUpdate,
    StationList,
    StationNewsResponse,
)
from app.schemas.playlist import PlaylistResponse
from app.services.perplexity import PerplexityClient, PerplexityError
from app.services.news_generator import NewsGenerator, NewsGenerationError

router = APIRouter(prefix="/api/stations", tags=["stations"])

# Default station image (guitar icon)
DEFAULT_IMAGE = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎸</text></svg>"


@router.get("", response_model=StationList)
async def get_stations(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Get all stations for the current user.
    
    Returns a list of all radio stations created by the authenticated user.
    """
    result = await session.execute(
        select(Station)
        .where(Station.user_id == current_user.id)
        .order_by(Station.created_at.desc())
    )
    stations = result.scalars().all()
    
    station_list = [
        StationRead(
            id=str(s.id),
            user_id=str(s.user_id),
            name=s.name,
            description=s.description,
            example_songs=s.example_songs or [],
            duration=s.duration,
            image_url=s.image_url or DEFAULT_IMAGE,
            play_news=s.play_news or False,
            play_news_at_start=s.play_news_at_start or False,
            news_interval_minutes=s.news_interval_minutes,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in stations
    ]
    
    return StationList(stations=station_list, total=len(station_list))


@router.post("", response_model=StationRead, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_data: StationCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Create a new radio station for the current user.
    
    If no image is provided, a default guitar icon will be assigned.
    """
    # Use default image if none provided
    image_url = station_data.image_url if station_data.image_url else DEFAULT_IMAGE
    
    station = Station(
        user_id=current_user.id,
        name=station_data.name,
        description=station_data.description,
        example_songs=station_data.example_songs or [],
        duration=station_data.duration,
        image_url=image_url,
        play_news=station_data.play_news,
        play_news_at_start=station_data.play_news_at_start,
        news_interval_minutes=station_data.news_interval_minutes,
    )
    
    session.add(station)
    await session.commit()
    await session.refresh(station)
    
    return StationRead(
        id=str(station.id),
        user_id=str(station.user_id),
        name=station.name,
        description=station.description,
        example_songs=station.example_songs or [],
        duration=station.duration,
        image_url=station.image_url,
        play_news=station.play_news or False,
        play_news_at_start=station.play_news_at_start or False,
        news_interval_minutes=station.news_interval_minutes,
        created_at=station.created_at,
        updated_at=station.updated_at,
    )


@router.get("/{station_id}", response_model=StationRead)
async def get_station(
    station_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Get a specific station by ID.
    
    Returns the station if it belongs to the current user.
    """
    result = await session.execute(
        select(Station).where(
            Station.id == station_id,
            Station.user_id == current_user.id
        )
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    return StationRead(
        id=str(station.id),
        user_id=str(station.user_id),
        name=station.name,
        description=station.description,
        example_songs=station.example_songs or [],
        duration=station.duration,
        image_url=station.image_url or DEFAULT_IMAGE,
        play_news=station.play_news or False,
        play_news_at_start=station.play_news_at_start or False,
        news_interval_minutes=station.news_interval_minutes,
        created_at=station.created_at,
        updated_at=station.updated_at,
    )


@router.put("/{station_id}", response_model=StationRead)
async def update_station(
    station_id: uuid.UUID,
    station_update: StationUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Update an existing station.
    
    Only provided fields will be updated.
    """
    result = await session.execute(
        select(Station).where(
            Station.id == station_id,
            Station.user_id == current_user.id
        )
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    # Update only provided fields
    update_data = station_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)
    
    # Ensure default image if explicitly set to None
    if station.image_url is None:
        station.image_url = DEFAULT_IMAGE
    
    await session.commit()
    await session.refresh(station)
    
    return StationRead(
        id=str(station.id),
        user_id=str(station.user_id),
        name=station.name,
        description=station.description,
        example_songs=station.example_songs or [],
        duration=station.duration,
        image_url=station.image_url,
        play_news=station.play_news or False,
        play_news_at_start=station.play_news_at_start or False,
        news_interval_minutes=station.news_interval_minutes,
        created_at=station.created_at,
        updated_at=station.updated_at,
    )


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Delete a station.
    
    Removes the station from the database.
    """
    result = await session.execute(
        select(Station).where(
            Station.id == station_id,
            Station.user_id == current_user.id
        )
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    await session.delete(station)
    await session.commit()


@router.post("/{station_id}/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(
    station_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Generate a playlist for a radio station.
    
    Uses Perplexity AI to create a playlist based on the station's
    name, description, example songs, and duration.
    """
    # Get the station
    result = await session.execute(
        select(Station).where(
            Station.id == station_id,
            Station.user_id == current_user.id
        )
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    try:
        # Generate playlist using Perplexity
        perplexity = PerplexityClient()
        playlist = await perplexity.generate_playlist(
            station_name=station.name,
            description=station.description or "",
            example_songs=station.example_songs or [],
            duration_hours=station.duration
        )
        
        # Add station_id to the playlist
        playlist['station_id'] = str(station.id)
        
        return PlaylistResponse(**playlist)
        
    except PerplexityError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate playlist: {str(e)}"
        )


@router.post("/{station_id}/generate-news", response_model=StationNewsResponse)
async def generate_station_news(
    station_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Generate news audio for a station.
    
    Uses user preferences to get personalized news.
    Can be called in advance to pre-cache the news.
    """
    # Get the station
    result = await session.execute(
        select(Station).where(
            Station.id == station_id,
            Station.user_id == current_user.id
        )
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    # Check if news is enabled for this station
    if not station.play_news:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="News playback is not enabled for this station"
        )
    
    try:
        # Generate news using the news generator service
        news_generator = NewsGenerator()
        news_data = await news_generator.generate_news_for_station(
            user_id=current_user.id,
            session=session
        )
        
        return StationNewsResponse(**news_data)
        
    except NewsGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate news: {str(e)}"
        )
