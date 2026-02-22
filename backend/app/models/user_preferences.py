"""
User Preferences model for storing news filtering preferences.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(Base):
    """
    User preferences model for news filtering.
    
    Stores preferences like country, location, topics, and keywords
    that will be used to filter news articles.
    """
    __tablename__ = "user_preferences"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Apple Music Subscription
    apple_music_connected: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    apple_music_subscription_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    apple_music_authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    apple_music_storefront: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="preferences")
    
    def __repr__(self) -> str:
        return f"<UserPreferences for user {self.user_id}>"
