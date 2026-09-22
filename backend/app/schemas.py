from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    name: str = Field(min_length=1)


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
    quiz_type: str = Field(default="diagnostic", pattern="^(diagnostic|checkpoint)$")
    


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

class MasteryDetail(BaseModel):
    topic_id: int
    topic_name: str
    mastery_score: float
    mastery_level: str
    last_updated: str


class MasteryOverviewResponse(BaseModel):
    user_id: int
    mastery: List[MasteryDetail]

class RoadmapTopicOut(BaseModel):
    topic_id: int
    topic_name: str
    domain: str
    difficulty: str
    order: int
    status: str
    mastery_score: float
    mastery_level: str
    estimated_duration: int
    is_unlocked: bool
    reason: str
    blocking_prerequisites: List[str] = []
    satisfied_prerequisites: List[str] = []


class RoadmapSummaryOut(BaseModel):
    total_topics: int
    scheduled_count: int
    mastered_count: int
    blocked_count: int
    deferred_count: int


class RoadmapResponse(BaseModel):
    user_id: int
    weekly_budget: int
    allocated_minutes: int
    remaining_budget: int
    next_topic: Optional[RoadmapTopicOut] = None
    roadmap: List[RoadmapTopicOut]
    summary: RoadmapSummaryOut


class NextTopicResponse(BaseModel):
    user_id: int
    next_topic: Optional[RoadmapTopicOut] = None
    reason: str


class LearningResourceOut(BaseModel):
    id: int
    topic_id: int
    title: str
    url: str
    format: str
    estimated_time: int
    difficulty: str


class ResourceRecommendationResponse(BaseModel):
    topic_id: int
    topic_name: str
    selected_arm: str
    resource: Optional[LearningResourceOut] = None
    ucb_score: float
    exploration_bonus: float
    context_features: Dict[str, float]
    interaction_id: Optional[int] = None


class BanditFeedbackRequest(BaseModel):
    user_id: int
    topic_id: int
    selected_arm: str
    pre_mastery: float
    post_mastery: float


class BanditFeedbackResponse(BaseModel):
    status: str
    reward: float
    pre_mastery: float
    post_mastery: float
    arm: str
    message: str