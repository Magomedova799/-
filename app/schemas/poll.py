from datetime import datetime
from pydantic import BaseModel, Field


class PollCreate(BaseModel):
    question: str = Field(min_length=5, max_length=300)
    options: list[str] = Field(min_length=2, max_length=1000)


class PollRead(BaseModel):
    id: int
    user_id: int
    question: str
    options: list[str]
    votes: dict[str, int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}