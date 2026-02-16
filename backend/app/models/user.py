"""
User model for authentication.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user_article import UserArticle
    from app.models.password_reset import PasswordReset
    from app.models.user_profile import UserProfile
    from app.models.user_preferences import UserPreferences
    from app.models.user_personalized_news import UserPersonalizedNews


class User(Base):
    """
    User model for authentication.
    
    Replaces fastapi-users SQLAlchemyBaseUserTableUUID with a custom model.
    """
    __tablename__ = "user"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user_articles: Mapped[list["UserArticle"]] = relationship(
        "UserArticle", back_populates="user", cascade="all, delete-orphan"
    )
    password_resets: Mapped[list["PasswordReset"]] = relationship(
        "PasswordReset", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreferences"] = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    personalized_news: Mapped[list["UserPersonalizedNews"]] = relationship(
        "UserPersonalizedNews", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
