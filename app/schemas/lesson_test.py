from pydantic import BaseModel


class QuestionCreate(BaseModel):
    question: str
    options: list[str]
    correct_option_index: int


class LessonTestCreate(BaseModel):
    lesson_id: int
    title: str
    questions: list[QuestionCreate]


class TestSubmit(BaseModel):
    answers: list[int]


class TestResultRead(BaseModel):
    id: int
    test_id: int
    score: int
    total_questions: int

    model_config = {"from_attributes": True}