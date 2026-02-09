import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    sub: Optional[str] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    password: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password."""
    token: str
    password: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
