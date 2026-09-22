"""
Path Planning Agent Package
A pure, framework-independent, domain-driven learning path planning module.
"""

from path_planning_agent.concept_graph import (
    ConceptGraph,
    CycleDetectedError,
)
from path_planning_agent.models import (
    DEFAULT_DIFFICULTY_DURATIONS,
    RoadmapItem,
    RoadmapResult,
    RoadmapStatus,
    StudentMastery,
    StudentProfile,
    TopicDifficulty,
    TopicNode,
)
from path_planning_agent.planner import (
    DEFAULT_MASTERY_THRESHOLD,
    PathPlanningAgent,
)
from path_planning_agent.providers import (
    ConceptGraphProvider,
    InMemoryProvider,
    MasteryProvider,
    StudentContextProvider,
)

__version__ = "1.0.0"

__all__ = [
    "PathPlanningAgent",
    "ConceptGraph",
    "CycleDetectedError",
    "TopicNode",
    "TopicDifficulty",
    "StudentMastery",
    "StudentProfile",
    "RoadmapItem",
    "RoadmapStatus",
    "RoadmapResult",
    "ConceptGraphProvider",
    "MasteryProvider",
    "StudentContextProvider",
    "InMemoryProvider",
    "DEFAULT_MASTERY_THRESHOLD",
    "DEFAULT_DIFFICULTY_DURATIONS",
]
