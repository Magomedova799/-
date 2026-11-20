from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)


class CourseRead(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    price: Decimal
    image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
