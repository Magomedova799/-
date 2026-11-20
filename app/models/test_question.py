
from sqlalchemy import ForeignKey, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("lesson_tests.id"),nullable=False)
    question: Mapped[str] = mapped_column(String(1000), nullable=False)
    options: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    correct_option_index: Mapped[int] = mapped_column(Integer,nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)