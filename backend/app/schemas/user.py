import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


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
