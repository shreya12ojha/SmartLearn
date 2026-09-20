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


from app.assessment_agent import score_quiz, InvalidUserError, InvalidSubmissionError


@router.post("/submit", response_model=QuizSubmitResponse)
def submit_quiz(payload: QuizSubmitRequest, db: Session = Depends(get_db)):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    try:
        mastery = score_quiz(db, payload.user_id, payload.answers, payload.quiz_type)
    except InvalidUserError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidSubmissionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return QuizSubmitResponse(mastery=mastery)

from app.models import TopicPrerequisite
from app.schemas import TopicGraphResponse, PrerequisiteOut


@router.get("/topics/graph", response_model=TopicGraphResponse)
def get_topic_graph(db: Session = Depends(get_db)):
    topics = db.query(Topic).all()
    prerequisites = db.query(TopicPrerequisite).all()

    topic_list = [{"id": t.id, "name": t.name, "domain": t.domain} for t in topics]
    prereq_list = [
        PrerequisiteOut(topic_id=p.topic_id, prerequisite_topic_id=p.prerequisite_topic_id)
        for p in prerequisites
    ]
    return TopicGraphResponse(topics=topic_list, prerequisites=prereq_list)