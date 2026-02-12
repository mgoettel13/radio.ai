"""
Pydantic schemas for user settings endpoints.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr


# Profile schemas
class ProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    age: Optional[int] = None
    country: Optional[str] = None
    language: Optional[str] = None


class ProfileRead(BaseModel):
    """Schema for reading user profile."""
    full_name: Optional[str] = None
    age: Optional[int] = None
    country: Optional[str] = None
    language: Optional[str] = None
    email: EmailStr  # From User model

    class Config:
        from_attributes = True


# Preferences schemas
class PreferencesUpdate(BaseModel):
    """Schema for updating user news preferences."""
    country: Optional[str] = None
    location: Optional[str] = None  # e.g., "Atlanta", "Georgia"
    topics: Optional[list[str]] = None
    keywords: Optional[list[str]] = None


class PreferencesRead(BaseModel):
    """Schema for reading user news preferences."""
    country: Optional[str] = None
    location: Optional[str] = None
    topics: list[str] = []
    keywords: list[str] = []

    class Config:
        from_attributes = True
