from datetime import datetime
from sqlalchemy import ForeignKey,DateTime,func,UniqueConstraint,CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"),nullable=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"),nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    course = relationship("Course",back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "course_id"),
        UniqueConstraint("user_id", "article_id"),
        UniqueConstraint("user_id", "project_id"),

        CheckConstraint(
            "((course_id IS NOT NULL)::int + "
            "(article_id IS NOT NULL)::int + "
            "(project_id IS NOT NULL)::int) = 1"
        ),
    )
