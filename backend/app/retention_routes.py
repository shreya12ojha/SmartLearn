from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, MasteryScore, Topic
from app.retention_agent import calculate_retention

router = APIRouter(prefix="/api/retention", tags=["Retention"])

@router.get("/revision-plan/{user_id}")
def get_revision_plan(
    user_id: int,
    simulated_days: float = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        db.query(MasteryScore, Topic)
        .join(Topic, MasteryScore.topic_id == Topic.id)
        .filter(MasteryScore.user_id == user_id)
        .all()
    )

    revisions = []

    for mastery, topic in rows:
        decay = calculate_retention(
            mastery.mastery_score,
            mastery.last_updated,
            simulated_days,
        )

        revisions.append({
            "topic_id": topic.id,
            "topic_name": topic.name,
            "original_mastery": mastery.mastery_score,
            **decay,
        })

    revisions.sort(key=lambda item: item["decayed_mastery"])

    return {
        "user_id": user_id,
        "simulated_days": simulated_days,
        "revision_topics": revisions,
    }