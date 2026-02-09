"""
Authentication router with login, register, and user endpoints.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token
from app.auth.service import (
    authenticate_user,
    create_user,
    get_current_active_user,
    get_user_by_email,
)
from app.config import get_settings
from app.database import get_async_session
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/jwt/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session),
):
    """
    OAuth2 compatible token login.
    
    Accepts form data with username (email) and password.
    Returns an access token for authentication.
    """
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/jwt/logout")
async def logout(
    current_user = Depends(get_current_active_user),
):
    """
    Logout endpoint.
    
    With JWT tokens, logout is primarily handled client-side by removing the token.
    This endpoint exists for API consistency and could be extended for token blacklisting.
    """
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Register a new user.
    
    Creates a new user account with the provided email and password.
    """
    # Check if user already exists
    existing_user = await get_user_by_email(session, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # Create new user
    user = await create_user(
        session=session,
        email=user_create.email,
        password=user_create.password,
    )
    
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user = Depends(get_current_active_user),
):
    """
    Get current user information.
    
    Returns the authenticated user's profile.
    """
    return UserRead.model_validate(current_user)


@router.get("/users/me", response_model=UserRead)
async def get_users_me(
    current_user = Depends(get_current_active_user),
):
    """
    Alternative endpoint for getting current user (for compatibility).
    
    This matches the fastapi-users endpoint path.
    """
    return UserRead.model_validate(current_user)
