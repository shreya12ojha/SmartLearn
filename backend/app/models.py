from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    weekly_time_budget = Column(Integer, default=300)   # in minutes
    preferred_format = Column(String, default="video")  # video/text/practice
    created_at = Column(DateTime, default=datetime.utcnow)

    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    mastery_scores = relationship("MasteryScore", back_populates="user")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    domain = Column(String, nullable=False)          # e.g. "DSA"
    difficulty_level = Column(String, default="Beginner")

    questions = relationship("QuizQuestion", back_populates="topic")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(String, nullable=False)
    options = Column(JSON, nullable=False)       # e.g. {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String, nullable=False)  # e.g. "B"
    difficulty = Column(String, default="medium")     # easy/medium/hard

    topic = relationship("Topic", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    quiz_type = Column(String, default="diagnostic")  # diagnostic/checkpoint
    score = Column(Float, nullable=False)             # normalized 0-1
    taken_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")


class MasteryScore(Base):
    __tablename__ = "mastery_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    mastery_level = Column(String, default="Beginner")  # Beginner/Intermediate/Advanced
    mastery_score = Column(Float, default=0.0)           # 0-1 continuous score
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="mastery_scores")

class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    prerequisite_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    format = Column(String, nullable=False, index=True)  # video, text, practice, interactive
    estimated_time = Column(Integer, default=30)         # in minutes
    difficulty = Column(String, default="medium")        # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("Topic", backref="resources")


class BanditInteraction(Base):
    __tablename__ = "bandit_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    selected_arm = Column(String, nullable=False)       # video, text, practice, interactive
    context = Column(JSON, nullable=False)              # feature vector serialized as list
    pre_mastery = Column(Float, nullable=False)         # mastery before study/attempt
    post_mastery = Column(Float, nullable=True)         # mastery after quiz attempt
    reward = Column(Float, nullable=True)               # post_mastery - pre_mastery
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    topic = relationship("Topic")


class BanditModelState(Base):
    """
    Persistent state for LinUCB bandit arms with database-level transactional concurrency.
    Each arm stores its positive-definite matrix A (d x d) and vector b (d).
    """
    __tablename__ = "bandit_model_state"

    id = Column(Integer, primary_key=True, index=True)
    arm_name = Column(String, unique=True, nullable=False, index=True)  # video, text, practice, interactive
    A_matrix = Column(JSON, nullable=False)  # list of lists (d x d)
    b_vector = Column(JSON, nullable=False)  # list of floats (d)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)