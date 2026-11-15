from datetime import datetime

from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    category_id: int | None = None


class ArticleRead(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    category_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}