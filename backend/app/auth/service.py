"""
Authentication service for user management and authentication.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token, get_password_hash, verify_password
from app.config import get_settings
from app.database import get_async_session

# Import User from models - will be created next
# This is done lazily to avoid circular imports
def get_user_model():
    from app.models.user import User
    return User


settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login", auto_error=False)


async def get_user_by_email(session: AsyncSession, email: str):
    """Get a user by email address."""
    User = get_user_model()
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID):
    """Get a user by ID."""
    User = get_user_model()
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str):
    """
    Authenticate a user by email and password.
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(session: AsyncSession, email: str, password: str, is_superuser: bool = False):
    """
    Create a new user.
    
    Args:
        session: Database session
        email: User email
        password: Plain text password
        is_superuser: Whether user is a superuser
        
    Returns:
        Created User object
    """
    User = get_user_model()
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        is_superuser=is_superuser,
        is_active=True,
        is_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_async_session),
):
    """
    Dependency to get the current authenticated user from JWT token.
    
    Returns None if no token provided (for optional authentication).
    Raises HTTPException if token is invalid.
    """
    if token is None:
        return None
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        uuid_obj = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_id(session, uuid_obj)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user),
):
    """
    Dependency to get the current active user.
    
    Raises HTTPException if user is not authenticated or not active.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user = Depends(get_current_active_user),
):
    """
    Dependency to get the current superuser.
    
    Raises HTTPException if user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
