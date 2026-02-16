import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.summary import Summary
    from app.models.user_article import UserArticle
    from app.models.user_personalized_news import UserPersonalizedNews


class Article(Base):
    __tablename__ = "article"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    guid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    link: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    summary: Mapped[Optional["Summary"]] = relationship(
        "Summary",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan"
    )
    user_articles: Mapped[list["UserArticle"]] = relationship(
        "UserArticle",
        back_populates="article",
        cascade="all, delete-orphan"
    )
    personalized_news: Mapped[list["UserPersonalizedNews"]] = relationship(
        "UserPersonalizedNews",
        back_populates="article",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Article {self.title[:50]}...>"
