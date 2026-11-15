from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.poll import Poll
from app.models.user import User
from app.schemas.poll import PollCreate, PollRead


router = APIRouter(
    prefix="/polls",
    tags=["Опросы"]
)


@router.post("/create", response_model=PollRead)
def create_poll(
    data: PollCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    options = [option.strip() for option in data.options]

    if any(not option for option in options):
        raise HTTPException(
            status_code=400,
            detail="Варианты ответов не могут быть пустыми"
        )

    if len(set(option.casefold() for option in options)) != len(options):
        raise HTTPException(
            status_code=400,
            detail="Варианты ответов не должны повторяться"
        )

    votes = {str(index): 0 for index in range(len(options))}

    poll = Poll(
        user_id=current_user.id,
        question=data.question,
        options=options,
        votes=votes
    )

    db.add(poll)
    db.commit()
    db.refresh(poll)

    return poll


@router.get("/all", response_model=list[PollRead])
def get_polls(db: Session = Depends(get_db)):
    return db.query(Poll).order_by(Poll.id.desc()).all()



@router.get("/{poll_id}", response_model=PollRead)
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()

    if poll is None:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    return poll



@router.post("/{poll_id}/vote")
def vote_poll(
    poll_id: int,
    option_index: int,
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == poll_id).with_for_update().first()

    if poll is None:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    if not poll.is_active:
        raise HTTPException(status_code=400, detail="Опрос закрыт")

    if option_index < 0 or option_index >= len(poll.options):
        raise HTTPException(status_code=400, detail="Неверный вариант ответа")

    votes = dict(poll.votes)
    key = str(option_index)
    votes[key] = votes.get(key, 0) + 1

    poll.votes = votes
    db.commit()

    return {
        "message": "Ваш голос учтён",
        "votes": poll.votes
    }


@router.patch("/{poll_id}/close")
def close_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    poll = db.query(Poll).filter(
        Poll.id == poll_id,
        Poll.user_id == current_user.id
    ).first()

    if poll is None:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    poll.is_active = False
    db.commit()

    return {"message": "Опрос закрыт"}