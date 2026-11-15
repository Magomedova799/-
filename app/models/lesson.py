from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"),nullable=False)
    title: Mapped[str] = mapped_column(String(200),nullable=False)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
