from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    lesson_id: int
    title: str
    content: str


class AssignmentRead(AssignmentCreate):
    id: int

    model_config = {"from_attributes": True}