import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.article import Article


class Summary(Base):
    __tablename__ = "summary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("article.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    model_used: Mapped[str] = mapped_column(
        String(50),
        default="sonar-pro",
        nullable=False
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="summary"
    )

    def __repr__(self) -> str:
        return f"<Summary for {self.article_id}>"
