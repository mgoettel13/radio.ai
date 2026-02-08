import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.database import User
    from app.models.article import Article


class UserArticle(Base):
    __tablename__ = "user_article"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("article.id", ondelete="CASCADE"),
        nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_articles"
    )
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="user_articles"
    )

    __table_args__ = (
        # Ensure a user can only have one entry per article
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<UserArticle user={self.user_id} article={self.article_id}>"
