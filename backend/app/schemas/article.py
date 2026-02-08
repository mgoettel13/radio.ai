import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class ArticleBase(BaseModel):
    title: str
    link: HttpUrl
    description: Optional[str] = None
    published_at: datetime
    author: Optional[str] = None
    category: Optional[str] = None


class ArticleCreate(ArticleBase):
    guid: str


class ArticleRead(ArticleBase):
    id: uuid.UUID
    guid: str
    fetched_at: datetime
    created_at: datetime
    has_summary: bool = False
    is_read: bool = False
    is_favorite: bool = False

    class Config:
        from_attributes = True


class ArticleList(BaseModel):
    items: list[ArticleRead]
    total: int
    last_updated: Optional[datetime] = None


class ArticleRefreshResponse(BaseModel):
    new_articles: int
    total_articles: int
    fetched_at: datetime
