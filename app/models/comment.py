from datetime import datetime
from sqlalchemy import (ForeignKey,DateTime,Text,func,CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"),nullable=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"),nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"),nullable=True)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    course = relationship("Course",back_populates="comments")
    __table_args__ = (
        CheckConstraint(
            "((course_id IS NOT NULL)::int + "
            "(article_id IS NOT NULL)::int + "
            "(project_id IS NOT NULL)::int) = 1"
        ),
    )
