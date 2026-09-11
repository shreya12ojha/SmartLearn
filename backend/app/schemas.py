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