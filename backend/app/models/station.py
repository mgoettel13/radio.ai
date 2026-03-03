"""
Station model for storing user-created radio stations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.played_music import PlayedMusic


class Station(Base):
    """
    Station model for storing user-created radio stations.
    
    Stores radio station configurations including name, description,
    example songs, duration, and optional image.
    """
    __tablename__ = "station"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_songs: Mapped[Optional[list]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    image_url: Mapped[Optional[str]] = mapped_column(String(50000), nullable=True)
    
    # News configuration
    play_news: Mapped[bool] = mapped_column(Boolean, default=False)
    play_news_at_start: Mapped[bool] = mapped_column(Boolean, default=False)
    news_interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 15, 30, or 60
    news_top_stories_count: Mapped[int] = mapped_column(Integer, default=3)  # 1-10, default 3
    news_max_length_minutes: Mapped[int] = mapped_column(Integer, default=3)  # 2-10, default 3
    
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
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="stations")
    played_music: Mapped[list["PlayedMusic"]] = relationship(
        "PlayedMusic", back_populates="station", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Station {self.name} for user {self.user_id}>"
