from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MasteryScore, Topic, User
from app.schemas import MasteryOverviewResponse, MasteryDetail

router = APIRouter(prefix="/api/assessment", tags=["Assessment"])


@router.get("/mastery/{user_id}", response_model=MasteryOverviewResponse)
def get_mastery_overview(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        db.query(MasteryScore, Topic)
        .join(Topic, MasteryScore.topic_id == Topic.id)
        .filter(MasteryScore.user_id == user_id)
        .all()
    )

    mastery_list = [
        MasteryDetail(
            topic_id=topic.id,
            topic_name=topic.name,
            mastery_score=mastery.mastery_score,
            mastery_level=mastery.mastery_level,
            last_updated=mastery.last_updated.isoformat(),
        )
        for mastery, topic in rows
    ]

    return MasteryOverviewResponse(user_id=user_id, mastery=mastery_list)