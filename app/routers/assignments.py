
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.assignment import Assignment
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentRead


router = APIRouter(
    prefix="/assignments",
    tags=["Задания"]
)



@router.post("/create", response_model=AssignmentRead)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(Lesson).filter(
        Lesson.id == data.lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Урок не найден"
        )

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=403,
            detail="У вас нет доступа к этому уроку"
        )

    assignments_count = db.query(Assignment).filter(
        Assignment.lesson_id == data.lesson_id
    ).count()

    if assignments_count >= 2:
        raise HTTPException(
            status_code=400,
            detail="К уроку можно добавить максимум два задания"
        )

    assignment = Assignment(
        lesson_id=data.lesson_id,
        title=data.title,
        content=data.content,
        position=assignments_count + 1
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment

@router.get("/lesson/{lesson_id}", response_model=list[AssignmentRead])
def get_lesson_assignments(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Урок не найден"
        )

    return db.query(Assignment).filter(
        Assignment.lesson_id == lesson_id
    ).order_by(Assignment.position.asc()).all()


@router.delete("/{assignment_id}/delete")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Задание не найдено"
        )

    lesson = db.query(Lesson).filter(
        Lesson.id == assignment.lesson_id
    ).first()

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=403,
            detail="У вас нет доступа к этому заданию"
        )

    db.delete(assignment)
    db.commit()

    return {"message": "Задание удалено"}
