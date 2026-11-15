from app.database import Base, engine

from app.models import (
    User,
    Category,
    Project,
    Article,
    Course,
    Lesson
)


Base.metadata.create_all(bind=engine)

print("Таблицы DevSpace успешно созданы!")