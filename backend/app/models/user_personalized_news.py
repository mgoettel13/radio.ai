"""
User Personalized News model for storing user's selected top 5 news based on preferences.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.article import Article


class UserPersonalizedNews(Base):
    """
    Stores the top 5 personalized news articles for each user.
    
    When user clicks "Get My News", the system:
    1. Refreshes RSS feed
    2. Uses Perplexity to rank articles based on user preferences
    3. Stores top 5 articles with rank position and timestamp
    """
    __tablename__ = "user_personalized_news"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"),
        nullable=False
    )
    rank_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )  # 1-5 indicating the rank
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="personalized_news")
    article: Mapped["Article"] = relationship("Article", back_populates="personalized_news")
    
    def __repr__(self) -> str:
        return f"<UserPersonalizedNews user={self.user_id} rank={self.rank_position}>"
