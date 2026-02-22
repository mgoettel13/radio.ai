"""
PlayedMusic model for tracking songs that have been played.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.station import Station


class PlayedMusic(Base):
    """
    Track played songs with play count and date.
    """
    __tablename__ = "played_music"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    station_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("station.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    song_id: Mapped[str] = mapped_column(String(100), nullable=False)  # Apple Music song ID
    artist: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    play_date: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    play_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="played_music")
    station: Mapped["Station"] = relationship("Station", back_populates="played_music")
    
    def __repr__(self) -> str:
        return f"<PlayedMusic {self.artist} - {self.title} for user {self.user_id}>"
