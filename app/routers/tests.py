
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.lesson_test import LessonTest
from app.models.test_question import TestQuestion
from app.models.test_attempt import TestAttempt
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.user import User
from app.schemas.lesson_test import (
    LessonTestCreate,
    TestSubmit,
    TestResultRead
)


router = APIRouter(
    prefix="/tests",
    tags=["Тесты"]
)



@router.post("/create")
def create_test(
    data: LessonTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not data.title.strip():
        raise HTTPException(400, "Введите название теста")

    if not data.questions:
        raise HTTPException(400, "Добавьте хотя бы один вопрос")

    lesson = db.query(Lesson).filter(
        Lesson.id == data.lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(404, "Урок не найден")

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(403, "Нет доступа к этому уроку")

    for question in data.questions:

        if not question.question.strip():
            raise HTTPException(400, "Заполните текст вопроса")

        if len(question.options) < 2:
            raise HTTPException(400, "Добавьте минимум два варианта ответа")

        for option in question.options:
            if not option.strip():
                raise HTTPException(400, "Варианты ответов не должны быть пустыми")

        if (
            question.correct_option_index < 0
            or question.correct_option_index >= len(question.options)
        ):
            raise HTTPException(400, "Выберите правильный вариант ответа")


    test = LessonTest(
        lesson_id=data.lesson_id,
        title=data.title.strip()
    )

    db.add(test)
    db.flush()

    for number, question_data in enumerate(data.questions, start=1):
        question = TestQuestion(
            test_id=test.id,
            question=question_data.question.strip(),
            options=[option.strip() for option in question_data.options],
            correct_option_index=question_data.correct_option_index,
            position=number
        )

        db.add(question)

    db.commit()
    db.refresh(test)

    return {
        "message": "Тест успешно создан",
        "test_id": test.id
    }


@router.get("/lesson/{lesson_id}")
def get_lesson_tests(
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

    tests = db.query(LessonTest).filter(
        LessonTest.lesson_id == lesson_id
    ).all()

    return tests



@router.get("/{test_id}")
def get_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    test = db.query(LessonTest).filter(
        LessonTest.id == test_id
    ).first()

    if test is None:
        raise HTTPException(
            status_code=404,
            detail="Тест не найден"
        )

    questions = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id
    ).order_by(TestQuestion.position.asc()).all()

    return {
        "id": test.id,
        "title": test.title,
        "questions": [
            {
                "id": question.id,
                "question": question.question,
                "options": question.options,
                "position": question.position
            }
            for question in questions
        ]
    }



@router.post("/{test_id}/submit", response_model=TestResultRead)
def submit_test(
    test_id: int,
    data: TestSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(LessonTest).filter(
        LessonTest.id == test_id
    ).first()

    if test is None:
        raise HTTPException(
            status_code=404,
            detail="Тест не найден"
        )

    questions = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id
    ).order_by(TestQuestion.position.asc()).all()

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="В тесте нет вопросов"
        )

    if len(data.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail="Количество ответов не совпадает с количеством вопросов"
        )

    score = 0

    for question, answer in zip(questions, data.answers):
        if answer < 0 or answer >= len(question.options):
            raise HTTPException(
                status_code=400,
                detail="Указан несуществующий вариант ответа"
            )

        if answer == question.correct_option_index:
            score += 1

    attempt = TestAttempt(
        test_id=test.id,
        user_id=current_user.id,
        answers=data.answers,
        score=score,
        total_questions=len(questions)
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


@router.get("/my-results", response_model=list[TestResultRead])
def get_my_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id
    ).order_by(TestAttempt.created_at.desc()).all()



@router.delete("/{test_id}/delete")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(LessonTest).filter(
        LessonTest.id == test_id
    ).first()

    if test is None:
        raise HTTPException(404, "Тест не найден")

    lesson = db.query(Lesson).filter(
        Lesson.id == test.lesson_id
    ).first()

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(403, "Нет доступа к этому тесту")

    db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id
    ).delete()

    db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id
    ).delete()

    db.delete(test)

    db.commit()

    return {"message": "Тест успешно удалён"}
