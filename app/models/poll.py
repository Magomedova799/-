from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)
    question: Mapped[str] = mapped_column(String(300),nullable=False)
    options: Mapped[list] = mapped_column(JSON,nullable=False)
    votes: Mapped[dict] = mapped_column(JSON,nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())