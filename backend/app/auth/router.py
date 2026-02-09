"""
Authentication router with login, register, and user endpoints.
"""

import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, get_password_hash
from app.auth.service import (
    authenticate_user,
    create_user,
    get_current_active_user,
    get_user_by_email,
)
from app.config import get_settings
from app.database import get_async_session
from app.models.password_reset import PasswordReset
from app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserRead,
)
from app.services.email import send_password_reset_email

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


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Request a password reset.
    
    Sends a password reset email if the user exists.
    Always returns success to prevent email enumeration.
    """
    # Find user by email
    user = await get_user_by_email(session, request.email)
    
    if user:
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=settings.password_reset_expire_hours)
        
        # Create password reset record
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
        )
        session.add(password_reset)
        await session.commit()
        
        # Send reset email
        send_password_reset_email(user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Reset password using a valid reset token.
    
    Validates the token and updates the user's password.
    """
    # Find the reset token
    result = await session.execute(
        select(PasswordReset).where(PasswordReset.token == request.token)
    )
    password_reset = result.scalar_one_or_none()
    
    # Validate token exists
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is valid (not expired and not used)
    if not password_reset.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get the user
    user = await get_user_by_email(session, password_reset.user.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update the user's password
    user.hashed_password = get_password_hash(request.password)
    
    # Mark token as used
    password_reset.used_at = datetime.utcnow()
    
    await session.commit()
    
    return MessageResponse(
        message="Password has been reset successfully"
    )
