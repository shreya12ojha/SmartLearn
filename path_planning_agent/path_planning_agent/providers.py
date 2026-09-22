from typing import Dict, Optional, Protocol, runtime_checkable

from path_planning_agent.concept_graph import ConceptGraph
from path_planning_agent.models import StudentMastery, StudentProfile


@runtime_checkable
class ConceptGraphProvider(Protocol):
    """Protocol for fetching the concept graph."""
    def get_concept_graph(self) -> ConceptGraph:
        ...


@runtime_checkable
class MasteryProvider(Protocol):
    """Protocol for fetching a student's topic mastery scores."""
    def get_mastery(self, user_id: str) -> Dict[str, StudentMastery]:
        ...


@runtime_checkable
class StudentContextProvider(Protocol):
    """Protocol for fetching a student's profile and time budget."""
    def get_student_context(self, user_id: str) -> StudentProfile:
        ...


class InMemoryProvider:
    """
    In-memory provider implementation for testing and standalone demos.
    Satisfies ConceptGraphProvider, MasteryProvider, and StudentContextProvider.
    """

    def __init__(
        self,
        graph: Optional[ConceptGraph] = None,
        mastery_data: Optional[Dict[str, Dict[str, StudentMastery]]] = None,
        profiles: Optional[Dict[str, StudentProfile]] = None,
    ):
        self.graph = graph or ConceptGraph()
        # user_id -> {topic_id -> StudentMastery}
        self.mastery_data = mastery_data or {}
        # user_id -> StudentProfile
        self.profiles = profiles or {}

    def get_concept_graph(self) -> ConceptGraph:
        return self.graph

    def get_mastery(self, user_id: str) -> Dict[str, StudentMastery]:
        return self.mastery_data.get(str(user_id), {})

    def get_student_context(self, user_id: str) -> StudentProfile:
        uid = str(user_id)
        if uid in self.profiles:
            return self.profiles[uid]
        # Return default profile with any registered mastery
        return StudentProfile(
            user_id=uid,
            weekly_time_budget=300,
            preferred_format="video",
            mastery_map=self.get_mastery(uid),
        )

    def set_student_mastery(self, user_id: str, topic_id: str, score: float, level: str = "Beginner") -> None:
        uid = str(user_id)
        tid = str(topic_id)
        if uid not in self.mastery_data:
            self.mastery_data[uid] = {}
        self.mastery_data[uid][tid] = StudentMastery(
            topic_id=tid,
            score=score,
            level=level,
            is_assessed=True,
        )

    def set_student_profile(self, profile: StudentProfile) -> None:
        self.profiles[str(profile.user_id)] = profile
