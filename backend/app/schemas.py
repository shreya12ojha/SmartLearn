from pydantic import BaseModel, EmailStr
from typing import List, Dict


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int


class QuestionOut(BaseModel):
    id: int
    question_text: str
    options: dict


class QuizResponse(BaseModel):
    questions: List[QuestionOut]


class AnswerItem(BaseModel):
    question_id: int
    selected_option: str


class QuizSubmitRequest(BaseModel):
    user_id: int
    answers: List[AnswerItem]


class QuizSubmitResponse(BaseModel):
    mastery: Dict[int, float]


class QuestionResultOut(BaseModel):
    question_id: int
    question_text: str
    selected_option: str
    correct_option: str
    is_correct: bool


class QuizSubmitResponse(BaseModel):
    mastery: Dict[int, float]
    results: List[QuestionResultOut]

class PrerequisiteOut(BaseModel):
    topic_id: int
    prerequisite_topic_id: int


class TopicGraphResponse(BaseModel):
    topics: List[dict]
    prerequisites: List[PrerequisiteOut]