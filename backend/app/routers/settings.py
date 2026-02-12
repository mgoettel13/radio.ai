"""
Settings router for user profile and preferences management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_active_user
from app.database import get_async_session
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_preferences import UserPreferences
from app.schemas.settings import (
    ProfileUpdate,
    ProfileRead,
    PreferencesUpdate,
    PreferencesRead,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/profile", response_model=ProfileRead)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Get the current user's profile.
    
    Returns profile information including email from the user account.
    Creates a default profile if one doesn't exist.
    """
    # Get or create profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # Create default profile
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    
    return ProfileRead(
        full_name=profile.full_name,
        age=profile.age,
        country=profile.country,
        language=profile.language,
        email=current_user.email,
    )


@router.put("/profile", response_model=ProfileRead)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Update the current user's profile.
    
    Only provided fields will be updated.
    """
    # Get or create profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # Create profile with update data
        profile = UserProfile(
            user_id=current_user.id,
            full_name=profile_update.full_name,
            age=profile_update.age,
            country=profile_update.country,
            language=profile_update.language,
        )
        session.add(profile)
    else:
        # Update existing profile
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
    
    await session.commit()
    await session.refresh(profile)
    
    return ProfileRead(
        full_name=profile.full_name,
        age=profile.age,
        country=profile.country,
        language=profile.language,
        email=current_user.email,
    )


@router.get("/preferences", response_model=PreferencesRead)
async def get_preferences(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Get the current user's news preferences.
    
    Returns preferences for news filtering.
    Creates default preferences if none exist.
    """
    # Get or create preferences
    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences
        preferences = UserPreferences(user_id=current_user.id)
        session.add(preferences)
        await session.commit()
        await session.refresh(preferences)
    
    return PreferencesRead(
        country=preferences.country,
        location=preferences.location,
        topics=preferences.topics or [],
        keywords=preferences.keywords or [],
    )


@router.put("/preferences", response_model=PreferencesRead)
async def update_preferences(
    preferences_update: PreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """
    Update the current user's news preferences.
    
    Only provided fields will be updated.
    """
    # Get or create preferences
    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create preferences with update data
        preferences = UserPreferences(
            user_id=current_user.id,
            country=preferences_update.country,
            location=preferences_update.location,
            topics=preferences_update.topics or [],
            keywords=preferences_update.keywords or [],
        )
        session.add(preferences)
    else:
        # Update existing preferences
        update_data = preferences_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
    
    await session.commit()
    await session.refresh(preferences)
    
    return PreferencesRead(
        country=preferences.country,
        location=preferences.location,
        topics=preferences.topics or [],
        keywords=preferences.keywords or [],
    )
