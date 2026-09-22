from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.cmab import bandit_service
from app.database import get_db
from app.models import MasteryScore, Topic, User
from app.path_planning_agent import get_student_next_topic, get_student_roadmap
from app.schemas import (
    BanditFeedbackRequest,
    BanditFeedbackResponse,
    LearningResourceOut,
    NextTopicResponse,
    ResourceRecommendationResponse,
    RoadmapResponse,
)

router = APIRouter(tags=["Path Planning & Recommendations"])


@router.get("/api/path-planning/roadmap/{user_id}", response_model=RoadmapResponse)
def get_roadmap_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access another student's roadmap")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    try:
        return get_student_roadmap(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")


@router.get("/api/path-planning/next-topic/{user_id}", response_model=NextTopicResponse)
def get_next_topic_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access another student's next topic")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    try:
        return get_student_next_topic(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error determining next topic: {str(e)}")


@router.get("/api/recommendations/resource", response_model=ResourceRecommendationResponse)
def get_resource_recommendation(
    user_id: int = Query(..., description="User ID"),
    topic_id: int = Query(..., description="Topic ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot request recommendations for another student")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mastery_row = (
        db.query(MasteryScore)
        .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id == topic_id)
        .first()
    )
    current_mastery = mastery_row.mastery_score if mastery_row else 0.0

    recommendation = bandit_service.recommend_resource_format(
        db=db, user=user, topic=topic, current_mastery=current_mastery,
    )

    resource_out = None
    if recommendation["resource"]:
        r = recommendation["resource"]
        resource_out = LearningResourceOut(
            id=r.id, topic_id=r.topic_id, title=r.title, url=r.url,
            format=r.format, estimated_time=r.estimated_time, difficulty=r.difficulty,
        )

    return ResourceRecommendationResponse(
        topic_id=topic.id,
        topic_name=topic.name,
        selected_arm=recommendation["selected_arm"],
        resource=resource_out,
        ucb_score=recommendation["ucb_score"],
        exploration_bonus=recommendation["exploration_bonus"],
        context_features=recommendation["context_features"],
        interaction_id=recommendation.get("interaction_id"),
    )


@router.post("/api/recommendations/feedback", response_model=BanditFeedbackResponse)
def post_bandit_feedback(
    payload: BanditFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot submit bandit feedback for another student")
    try:
        result = bandit_service.update_model(
            db=db, user_id=payload.user_id, topic_id=payload.topic_id,
            selected_arm=payload.selected_arm, pre_mastery=payload.pre_mastery, post_mastery=payload.post_mastery,
        )
        return BanditFeedbackResponse(
            status="success", reward=result["reward"], pre_mastery=result["pre_mastery"],
            post_mastery=result["post_mastery"], arm=result["arm"],
            message=f"LinUCB model updated for arm '{result['arm']}' with reward {result['reward']:+.3f}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update bandit: {str(e)}")
