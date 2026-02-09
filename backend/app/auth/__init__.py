"""
Authentication module for FastAPI built-in auth.
"""

from app.auth.router import router as auth_router
from app.auth.service import get_current_user, get_current_active_user, get_current_superuser

__all__ = [
    "auth_router",
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
]
