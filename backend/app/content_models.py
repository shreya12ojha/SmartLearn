from sqlalchemy import Column, Integer, String, ForeignKey
from app.models import Base

class ContentResource(Base):
    __tablename__ = "content_resources"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    platform = Column(String, nullable=False)       # YouTube, GeeksForGeeks, LeetCode
    format = Column(String, nullable=False)         # video, article, practice
    difficulty = Column(String, nullable=False)     # Beginner, Intermediate, Advanced
    estimated_minutes = Column(Integer, default=15)
    description = Column(String)