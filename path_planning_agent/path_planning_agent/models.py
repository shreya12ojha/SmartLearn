from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class RoadmapStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    MASTERED = "MASTERED"
    BLOCKED = "BLOCKED"
    DEFERRED = "DEFERRED"


class TopicDifficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


# Standard duration fallback in minutes based on difficulty
DEFAULT_DIFFICULTY_DURATIONS: Dict[str, int] = {
    TopicDifficulty.BEGINNER.value: 30,
    TopicDifficulty.INTERMEDIATE.value: 60,
    TopicDifficulty.ADVANCED.value: 90,
}


@dataclass
class TopicNode:
    id: str
    name: str
    domain: str = "DSA"
    difficulty: str = TopicDifficulty.BEGINNER.value
    estimated_duration: Optional[int] = None  # in minutes
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_duration(self) -> int:
        if self.estimated_duration is not None and self.estimated_duration > 0:
            return self.estimated_duration
        # Match case-insensitively or return default 60
        diff_key = self.difficulty.capitalize() if self.difficulty else "Beginner"
        return DEFAULT_DIFFICULTY_DURATIONS.get(diff_key, 60)


@dataclass
class StudentMastery:
    topic_id: str
    score: float = 0.0  # 0.0 to 1.0 continuous score
    level: str = "Beginner"  # Beginner, Intermediate, Advanced
    is_assessed: bool = False
    last_updated: Optional[str] = None


@dataclass
class StudentProfile:
    user_id: str
    weekly_time_budget: int = 300  # in minutes
    preferred_format: str = "video"  # video, text, practice, interactive
    mastery_map: Dict[str, StudentMastery] = field(default_factory=dict)


@dataclass
class RoadmapItem:
    topic: TopicNode
    order: int
    status: RoadmapStatus
    mastery_score: float
    mastery_level: str
    estimated_duration: int
    is_unlocked: bool
    reason: str
    blocking_prerequisites: List[str] = field(default_factory=list)
    satisfied_prerequisites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic.id,
            "topic_name": self.topic.name,
            "domain": self.topic.domain,
            "difficulty": self.topic.difficulty,
            "order": self.order,
            "status": self.status.value,
            "mastery_score": round(self.mastery_score, 3),
            "mastery_level": self.mastery_level,
            "estimated_duration": self.estimated_duration,
            "is_unlocked": self.is_unlocked,
            "reason": self.reason,
            "blocking_prerequisites": self.blocking_prerequisites,
            "satisfied_prerequisites": self.satisfied_prerequisites,
        }


@dataclass
class RoadmapResult:
    user_id: str
    weekly_budget: int
    allocated_minutes: int
    remaining_budget: int
    items: List[RoadmapItem] = field(default_factory=list)
    next_recommended_topic: Optional[RoadmapItem] = None

    @property
    def scheduled_items(self) -> List[RoadmapItem]:
        return [item for item in self.items if item.status == RoadmapStatus.SCHEDULED]

    @property
    def mastered_items(self) -> List[RoadmapItem]:
        return [item for item in self.items if item.status == RoadmapStatus.MASTERED]

    @property
    def blocked_items(self) -> List[RoadmapItem]:
        return [item for item in self.items if item.status == RoadmapStatus.BLOCKED]

    @property
    def deferred_items(self) -> List[RoadmapItem]:
        return [item for item in self.items if item.status == RoadmapStatus.DEFERRED]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "weekly_budget": self.weekly_budget,
            "allocated_minutes": self.allocated_minutes,
            "remaining_budget": self.remaining_budget,
            "next_topic": self.next_recommended_topic.to_dict() if self.next_recommended_topic else None,
            "items": [item.to_dict() for item in self.items],
            "summary": {
                "total_topics": len(self.items),
                "scheduled_count": len(self.scheduled_items),
                "mastered_count": len(self.mastered_items),
                "blocked_count": len(self.blocked_items),
                "deferred_count": len(self.deferred_items),
            },
        }
