import sys
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

# Ensure path_planning_agent is importable
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir / "path_planning_agent") not in sys.path:
    sys.path.insert(0, str(root_dir / "path_planning_agent"))

from path_planning_agent.concept_graph import ConceptGraph
from path_planning_agent.models import (
    RoadmapItem,
    RoadmapResult,
    RoadmapStatus,
    StudentMastery,
    StudentProfile,
    TopicNode,
)
from path_planning_agent.planner import PathPlanningAgent
from path_planning_agent.providers import (
    ConceptGraphProvider,
    MasteryProvider,
    StudentContextProvider,
)

from app.models import MasteryScore, Topic, TopicPrerequisite, User
from app.schemas import (
    NextTopicResponse,
    RoadmapResponse,
    RoadmapSummaryOut,
    RoadmapTopicOut,
)

# Authoritative threshold matching assessment_agent.py
AUTHORITATIVE_MASTERY_THRESHOLD = 0.75


# ============================================================
# SmartLearn SQLAlchemy Adapters
# ============================================================

class SQLAlchemyConceptGraphProvider(ConceptGraphProvider):
    """Fetches topics and prerequisite edges from SmartLearn database."""

    def __init__(self, db: Session):
        self.db = db

    def get_concept_graph(self) -> ConceptGraph:
        graph = ConceptGraph()
        topics = self.db.query(Topic).all()
        for t in topics:
            node = TopicNode(
                id=str(t.id),
                name=t.name,
                domain=t.domain,
                difficulty=t.difficulty_level or "Beginner",
            )
            graph.add_topic(node)

        prerequisites = self.db.query(TopicPrerequisite).all()
        for p in prerequisites:
            try:
                graph.add_prerequisite(
                    topic_id=str(p.topic_id),
                    prerequisite_topic_id=str(p.prerequisite_topic_id),
                )
            except KeyError:
                # Skip if either topic is not in the database
                continue

        return graph


class SQLAlchemyMasteryProvider(MasteryProvider):
    """Fetches student mastery scores from SmartLearn database."""

    def __init__(self, db: Session):
        self.db = db

    def get_mastery(self, user_id: str) -> Dict[str, StudentMastery]:
        uid = int(user_id)
        scores = (
            self.db.query(MasteryScore)
            .filter(MasteryScore.user_id == uid)
            .all()
        )
        result = {}
        for s in scores:
            result[str(s.topic_id)] = StudentMastery(
                topic_id=str(s.topic_id),
                score=s.mastery_score,
                level=s.mastery_level or "Beginner",
                is_assessed=True,
                last_updated=s.last_updated.isoformat() if s.last_updated else None,
            )
        return result


class SQLAlchemyStudentContextProvider(StudentContextProvider):
    """Fetches student weekly budget and preferences from SmartLearn database."""

    def __init__(self, db: Session):
        self.db = db

    def get_student_context(self, user_id: str) -> StudentProfile:
        uid = int(user_id)
        user = self.db.query(User).filter(User.id == uid).first()
        if not user:
            return StudentProfile(user_id=str(uid), weekly_time_budget=300, preferred_format="video")

        return StudentProfile(
            user_id=str(user.id),
            weekly_time_budget=user.weekly_time_budget or 300,
            preferred_format=user.preferred_format or "video",
        )


# ============================================================
# Production Service Functions
# ============================================================

def get_student_roadmap(db: Session, user_id: int) -> RoadmapResponse:
    """
    Generates the complete personalized roadmap for a student.
    Integrates Concept Graph, Mastery, and Weekly Budget.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")

    graph_provider = SQLAlchemyConceptGraphProvider(db)
    mastery_provider = SQLAlchemyMasteryProvider(db)
    context_provider = SQLAlchemyStudentContextProvider(db)

    agent = PathPlanningAgent(
        graph_provider=graph_provider,
        mastery_provider=mastery_provider,
        context_provider=context_provider,
        mastery_threshold=AUTHORITATIVE_MASTERY_THRESHOLD,
    )

    roadmap_result: RoadmapResult = agent.generate_roadmap(user_id=user_id)

    # Convert domain items to Pydantic response models
    topic_outs: List[RoadmapTopicOut] = []
    for item in roadmap_result.items:
        topic_outs.append(
            RoadmapTopicOut(
                topic_id=int(item.topic.id),
                topic_name=item.topic.name,
                domain=item.topic.domain,
                difficulty=item.topic.difficulty,
                order=item.order,
                status=item.status.value,
                mastery_score=item.mastery_score,
                mastery_level=item.mastery_level,
                estimated_duration=item.estimated_duration,
                is_unlocked=item.is_unlocked,
                reason=item.reason,
                blocking_prerequisites=item.blocking_prerequisites,
                satisfied_prerequisites=item.satisfied_prerequisites,
            )
        )

    next_out: Optional[RoadmapTopicOut] = None
    if roadmap_result.next_recommended_topic:
        nxt = roadmap_result.next_recommended_topic
        next_out = RoadmapTopicOut(
            topic_id=int(nxt.topic.id),
            topic_name=nxt.topic.name,
            domain=nxt.topic.domain,
            difficulty=nxt.topic.difficulty,
            order=nxt.order,
            status=nxt.status.value,
            mastery_score=nxt.mastery_score,
            mastery_level=nxt.mastery_level,
            estimated_duration=nxt.estimated_duration,
            is_unlocked=nxt.is_unlocked,
            reason=nxt.reason,
            blocking_prerequisites=nxt.blocking_prerequisites,
            satisfied_prerequisites=nxt.satisfied_prerequisites,
        )

    summary = RoadmapSummaryOut(
        total_topics=len(roadmap_result.items),
        scheduled_count=len(roadmap_result.scheduled_items),
        mastered_count=len(roadmap_result.mastered_items),
        blocked_count=len(roadmap_result.blocked_items),
        deferred_count=len(roadmap_result.deferred_items),
    )

    return RoadmapResponse(
        user_id=user_id,
        weekly_budget=roadmap_result.weekly_budget,
        allocated_minutes=roadmap_result.allocated_minutes,
        remaining_budget=roadmap_result.remaining_budget,
        next_topic=next_out,
        roadmap=topic_outs,
        summary=summary,
    )


def get_student_next_topic(db: Session, user_id: int) -> NextTopicResponse:
    """
    Returns only the next actionable topic for the student.
    """
    roadmap = get_student_roadmap(db, user_id)
    if roadmap.next_topic:
        reason = (
            f"Prerequisites satisfied and current mastery ({round(roadmap.next_topic.mastery_score * 100)}%) "
            f"is below the {int(AUTHORITATIVE_MASTERY_THRESHOLD * 100)}% threshold."
        )
    else:
        reason = "All available topics have been sufficiently mastered or are blocked."

    return NextTopicResponse(
        user_id=user_id,
        next_topic=roadmap.next_topic,
        reason=reason,
    )
