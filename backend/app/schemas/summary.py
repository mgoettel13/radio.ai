import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SummaryBase(BaseModel):
    content: str
    model_used: str = "sonar-pro"
    tokens_used: Optional[int] = None


class SummaryCreate(SummaryBase):
    article_id: uuid.UUID


class SummaryRead(SummaryBase):
    id: uuid.UUID
    article_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
