from pydantic import BaseModel, Field


class LessonCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    position: int = Field(ge=1)
    video_url: str | None = None


class LessonRead(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    position: int
    image_url: str | None = None
    video_url: str | None = None


class LessonUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    position: int = Field(ge=1)
    video_url: str | None = None

    model_config = {"from_attributes": True}
