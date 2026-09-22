from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.cmab import bandit_service
from app.database import get_db
from app.models import LearningResource, MasteryScore, Topic, User
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


# ============================================================
# Path Planning Endpoints
# ============================================================

@router.get("/api/path-planning/roadmap/{user_id}", response_model=RoadmapResponse)
def get_roadmap_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Returns the personalized learning roadmap for a student.
    Evaluates concept graph, prerequisites, student mastery, and weekly budget.
    """
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access another student's roadmap")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    try:
        roadmap = get_student_roadmap(db, user_id)
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")


@router.get("/api/path-planning/next-topic/{user_id}", response_model=NextTopicResponse)
def get_next_topic_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Returns the next actionable topic for the student based on prerequisite unlocking and budget.
    """
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access another student's next topic")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    try:
        next_topic_data = get_student_next_topic(db, user_id)
        return next_topic_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error determining next topic: {str(e)}")


# ============================================================
# CMAB / Resource Recommendation Endpoints
# ============================================================

@router.get("/api/recommendations/resource", response_model=ResourceRecommendationResponse)
def get_resource_recommendation(
    user_id: int = Query(..., description="User ID"),
    topic_id: int = Query(..., description="Topic ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Selects the optimal learning format (video, text, practice, interactive) for the student
    using LinUCB Contextual Multi-Armed Bandit, and retrieves a matching LearningResource.
    """
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot request recommendations for another student")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Fetch current mastery score if available
    mastery_row = (
        db.query(MasteryScore)
        .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id == topic_id)
        .first()
    )
    current_mastery = mastery_row.mastery_score if mastery_row else 0.0

    recommendation = bandit_service.recommend_resource_format(
        db=db,
        user=user,
        topic=topic,
        current_mastery=current_mastery,
    )

    resource_out = None
    if recommendation["resource"]:
        r = recommendation["resource"]
        resource_out = LearningResourceOut(
            id=r.id,
            topic_id=r.topic_id,
            title=r.title,
            url=r.url,
            format=r.format,
            estimated_time=r.estimated_time,
            difficulty=r.difficulty,
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
    """
    Ingests learning reward (post_mastery - pre_mastery) following a quiz attempt
    and updates the LinUCB model parameters with row-level transaction safety.
    """
    if current_user and current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot submit bandit feedback for another student")
    try:
        result = bandit_service.update_model(
            db=db,
            user_id=payload.user_id,
            topic_id=payload.topic_id,
            selected_arm=payload.selected_arm,
            pre_mastery=payload.pre_mastery,
            post_mastery=payload.post_mastery,
        )
        return BanditFeedbackResponse(
            status="success",
            reward=result["reward"],
            pre_mastery=result["pre_mastery"],
            post_mastery=result["post_mastery"],
            arm=result["arm"],
            message=f"LinUCB model updated for arm '{result['arm']}' with reward {result['reward']:+.3f}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update bandit: {str(e)}")


# ============================================================
# Learning Resources Listing
# ============================================================

@router.get("/api/resources", response_model=List[LearningResourceOut])
def list_resources(
    topic_id: Optional[int] = Query(None, description="Optional filter by Topic ID"),
    format: Optional[str] = Query(None, description="Optional filter by format (video/text/practice/interactive)"),
    db: Session = Depends(get_db),
):
    """
    Lists learning resources, optionally filtered by topic and format.
    Satisfies frontend TODO: GET /api/resources?topic_id=
    """
    query = db.query(LearningResource)
    if topic_id is not None:
        query = query.filter(LearningResource.topic_id == topic_id)
    if format:
        query = query.filter(LearningResource.format == format.lower())

    resources = query.all()
    return [
        LearningResourceOut(
            id=r.id,
            topic_id=r.topic_id,
            title=r.title,
            url=r.url,
            format=r.format,
            estimated_time=r.estimated_time,
            difficulty=r.difficulty,
        )
        for r in resources
    ]
