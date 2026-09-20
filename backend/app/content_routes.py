from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Topic, User
from app.content_models import ContentResource

router = APIRouter(prefix="/api/resources", tags=["Content Curation"])

@router.get("")
def get_resources(topic_id: int, user_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    user = db.query(User).filter(User.id == user_id).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resources = db.query(ContentResource).filter(
        ContentResource.topic_id == topic_id
    ).all()

    # Preferred format appears first.
    resources.sort(key=lambda resource: resource.format != user.preferred_format)

    return {
        "topic_id": topic.id,
        "topic_name": topic.name,
        "recommended_resources": resources,
    }