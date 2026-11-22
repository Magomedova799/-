
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user

from app.models.lesson_test import LessonTest
from app.models.test_question import TestQuestion
from app.models.test_attempt import TestAttempt
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.user import User

from app.schemas.lesson_test import TestResultRead


router = APIRouter(
    prefix="/tests",
    tags=["Тесты"]
)

templates = Jinja2Templates(directory="templates")



@router.get("/create-page")
def test_create_page(
    request: Request,
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(404, "Урок не найден")

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(403, "Нет доступа к уроку")

    return templates.TemplateResponse(
        request=request,
        name="test_create.html",
        context={"lesson": lesson}
    )




@router.post("/create-form")
async def create_test_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = await request.form()

    try:
        lesson_id = int(form.get("lesson_id"))
    except (ValueError, TypeError):
        raise HTTPException(400, "Некорректный урок")

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(404, "Урок не найден")

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(403, "Нет доступа к уроку")

    title = str(form.get("title", "")).strip()
    description = str(form.get("description", "")).strip()

    if not title:
        raise HTTPException(400, "Введите название теста")

    questions_data = []

    for number in range(1, 6):

        question_text = str(
            form.get(f"question_{number}", "")
        ).strip()

        options_raw = [
            str(form.get(f"option_{number}_{i}", "")).strip()
            for i in range(1, 5)
        ]

        correct_raw = form.get(f"correct_{number}")

        if not question_text:
            if any(options_raw) or correct_raw is not None:
                raise HTTPException(
                    400,
                    detail=f"Заполните текст вопроса №{number}"
                )
            continue

        nonempty_indices = [
            i for i, option in enumerate(options_raw)
            if option
        ]

        options = [
            options_raw[i] for i in nonempty_indices
        ]

        if len(options) < 2:
            raise HTTPException(
                400,
                detail=f"У вопроса №{number} должно быть минимум два варианта ответа"
            )

        if correct_raw is None:
            raise HTTPException(
                400,
                detail=f"Выберите правильный ответ для вопроса №{number}"
            )

        try:
            correct_original_index = int(correct_raw)
        except (ValueError, TypeError):
            raise HTTPException(
                400,
                "Некорректный правильный ответ"
            )

        if correct_original_index not in range(4):
            raise HTTPException(
                400,
                "Некорректный правильный ответ"
            )

        if correct_original_index not in nonempty_indices:
            raise HTTPException(
                400,
                detail=f"Правильный вариант вопроса №{number} не заполнен"
            )

        correct_index = nonempty_indices.index(
            correct_original_index
        )

        questions_data.append({
            "question": question_text,
            "options": options,
            "correct_option_index": correct_index,
            "position": len(questions_data) + 1
        })

    if not questions_data:
        raise HTTPException(
            400,
            detail="Добавьте хотя бы один вопрос или пропустите создание теста"
        )

    test = LessonTest(
        lesson_id=lesson_id,
        title=title,
        description=description or None
    )

    db.add(test)
    db.flush()

    for item in questions_data:
        question = TestQuestion(
            test_id=test.id,
            question=item["question"],
            options=item["options"],
            correct_option_index=item["correct_option_index"],
            position=item["position"]
        )

        db.add(question)

    db.commit()

    return RedirectResponse(
        url=f"/assignments/create-page?lesson_id={lesson_id}",
        status_code=303
    )




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




@router.get("/my-results", response_model=list[TestResultRead])
def get_my_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id
    ).order_by(
        TestAttempt.created_at.desc()
    ).all()



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
    ).order_by(
        TestQuestion.position.asc()
    ).all()

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




@router.post("/{test_id}/submit-form")
async def submit_test_form(
    test_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(LessonTest).filter(
        LessonTest.id == test_id
    ).first()

    if test is None:
        raise HTTPException(404, "Тест не найден")

    questions = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id
    ).order_by(
        TestQuestion.position.asc()
    ).all()

    if not questions:
        raise HTTPException(
            400,
            "В тесте нет вопросов"
        )

    form = await request.form()

    answers = []
    score = 0

    for question in questions:

        answer_value = form.get(
            f"question_{question.id}"
        )

        if answer_value is None:
            raise HTTPException(
                400,
                detail=f"Ответьте на вопрос: {question.question}"
            )

        try:
            answer = int(answer_value)
        except (ValueError, TypeError):
            raise HTTPException(
                400,
                detail="Некорректный вариант ответа"
            )

        if answer < 0 or answer >= len(question.options):
            raise HTTPException(
                400,
                detail="Несуществующий вариант ответа"
            )

        answers.append(answer)

        if answer == question.correct_option_index:
            score += 1

    attempt = TestAttempt(
        test_id=test.id,
        user_id=current_user.id,
        answers=answers,
        score=score,
        total_questions=len(questions)
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return templates.TemplateResponse(
        request=request,
        name="test_result.html",
        context={
            "test": test,
            "score": score,
            "total_questions": len(questions)
        }
    )



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

    if lesson is None:
        raise HTTPException(404, "Урок не найден")

    course = db.query(Course).filter(
        Course.id == lesson.course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(
            403,
            "Нет доступа к этому тесту"
        )

    db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id
    ).delete()

    db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id
    ).delete()

    db.delete(test)
    db.commit()

    return {"message": "Тест успешно удалён"}

