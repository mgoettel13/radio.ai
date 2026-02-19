"""
Station model for storing user-created radio stations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


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
    
    def __repr__(self) -> str:
        return f"<Station {self.name} for user {self.user_id}>"
