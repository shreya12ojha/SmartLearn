from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QuizQuestion, Topic
from app.schemas import QuizResponse, QuestionOut, QuizSubmitRequest, QuizSubmitResponse
from app.assessment_agent import score_quiz

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.get("", response_model=QuizResponse)
def get_quiz(topic: int = Query(..., description="Topic ID"), db: Session = Depends(get_db)):
    topic_obj = db.query(Topic).filter(Topic.id == topic).first()
    if not topic_obj:
        raise HTTPException(status_code=404, detail="Topic not found")

    questions = db.query(QuizQuestion).filter(QuizQuestion.topic_id == topic).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this topic")

    question_list = [
        QuestionOut(id=q.id, question_text=q.question_text, options=q.options)
        for q in questions
    ]
    return QuizResponse(questions=question_list)


@router.post("/submit", response_model=QuizSubmitResponse)
def submit_quiz(payload: QuizSubmitRequest, db: Session = Depends(get_db)):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    mastery = score_quiz(db, payload.user_id, payload.answers)
    return QuizSubmitResponse(mastery=mastery)