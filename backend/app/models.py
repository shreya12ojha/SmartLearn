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