from typing import Dict, List, Optional, Union

from path_planning_agent.concept_graph import ConceptGraph
from path_planning_agent.models import (
    RoadmapItem,
    RoadmapResult,
    RoadmapStatus,
    StudentMastery,
    StudentProfile,
    TopicNode,
)
from path_planning_agent.providers import (
    ConceptGraphProvider,
    MasteryProvider,
    StudentContextProvider,
)

DEFAULT_MASTERY_THRESHOLD = 0.75


class PathPlanningAgent:
    """
    Path Planning Agent responsible for answering:
    'What should the student study next?'

    Operates strictly on normalized domain models and provider abstractions.
    """

    def __init__(
        self,
        graph_provider: Optional[ConceptGraphProvider] = None,
        mastery_provider: Optional[MasteryProvider] = None,
        context_provider: Optional[StudentContextProvider] = None,
        mastery_threshold: float = DEFAULT_MASTERY_THRESHOLD,
    ):
        self.graph_provider = graph_provider
        self.mastery_provider = mastery_provider
        self.context_provider = context_provider
        self.mastery_threshold = mastery_threshold

    def classify_mastery_tier(self, score: float, is_assessed: bool) -> str:
        """
        Classifies mastery according to authoritative assessment thresholds:
        - Unassessed: not attempted yet
        - Beginner / Weak: < 0.40
        - Intermediate / Developing: 0.40 <= score < 0.75
        - Advanced / Mastered: >= 0.75
        """
        if not is_assessed:
            return "Unassessed"
        if score < 0.40:
            return "Beginner"
        elif score < self.mastery_threshold:
            return "Intermediate"
        else:
            return "Advanced"

    def generate_roadmap(
        self,
        user_id: Union[str, int],
        graph: Optional[ConceptGraph] = None,
        mastery_map: Optional[Dict[str, StudentMastery]] = None,
        time_budget: Optional[int] = None,
    ) -> RoadmapResult:
        """
        Generates a personalized, time-budgeted, prerequisite-gated learning roadmap.
        """
        uid = str(user_id)

        # 1. Resolve Concept Graph
        concept_graph = graph
        if concept_graph is None and self.graph_provider:
            concept_graph = self.graph_provider.get_concept_graph()
        if concept_graph is None:
            raise ValueError("No ConceptGraph provided or available from provider")

        # 2. Resolve Student Context & Mastery
        resolved_mastery: Dict[str, StudentMastery] = {}
        if mastery_map is not None:
            resolved_mastery = {str(k): v for k, v in mastery_map.items()}
        elif self.mastery_provider:
            resolved_mastery = self.mastery_provider.get_mastery(uid)

        student_budget = time_budget
        if student_budget is None and self.context_provider:
            profile = self.context_provider.get_student_context(uid)
            student_budget = profile.weekly_time_budget
        if student_budget is None or student_budget <= 0:
            student_budget = 300  # Default to 300 minutes

        # Build quick lookup for numerical mastery scores
        mastery_scores: Dict[str, float] = {
            tid: m.score for tid, m in resolved_mastery.items()
        }

        # 3. Topologically order topics
        ordered_topics: List[TopicNode] = concept_graph.topological_sort()

        items: List[RoadmapItem] = []
        allocated_minutes = 0
        order_counter = 1
        next_topic: Optional[RoadmapItem] = None

        # 4. Evaluate each topic in topological order
        for topic in ordered_topics:
            tid = str(topic.id)
            duration = topic.get_duration()
            mastery_obj = resolved_mastery.get(tid)
            score = mastery_obj.score if mastery_obj else 0.0
            is_assessed = mastery_obj.is_assessed if mastery_obj else False
            level = self.classify_mastery_tier(score, is_assessed)

            # Check prerequisite unlocking
            is_unlocked = concept_graph.is_unlocked(tid, mastery_scores, self.mastery_threshold)
            blocking_prereqs = concept_graph.get_blocking_prerequisites(
                tid, mastery_scores, self.mastery_threshold
            )
            immediate_prereqs = concept_graph.get_immediate_prerequisites(tid)
            satisfied_prereqs = [
                concept_graph.get_topic(p).name
                for p in immediate_prereqs
                if concept_graph.get_topic(p) and mastery_scores.get(p, 0.0) >= self.mastery_threshold
            ]
            blocking_desc = [
                f"{name} ({round(s * 100)}% < {int(self.mastery_threshold * 100)}%)"
                for _, name, s in blocking_prereqs
            ]

            # Case A: Topic is already sufficiently mastered
            if score >= self.mastery_threshold:
                item = RoadmapItem(
                    topic=topic,
                    order=order_counter,
                    status=RoadmapStatus.MASTERED,
                    mastery_score=score,
                    mastery_level=level,
                    estimated_duration=duration,
                    is_unlocked=True,
                    reason=f"Mastered: score of {round(score * 100)}% meets or exceeds the {int(self.mastery_threshold * 100)}% threshold.",
                    blocking_prerequisites=[],
                    satisfied_prerequisites=satisfied_prereqs,
                )
                items.append(item)
                order_counter += 1
                continue

            # Case B: Prerequisites not satisfied -> Blocked
            if not is_unlocked:
                item = RoadmapItem(
                    topic=topic,
                    order=order_counter,
                    status=RoadmapStatus.BLOCKED,
                    mastery_score=score,
                    mastery_level=level,
                    estimated_duration=duration,
                    is_unlocked=False,
                    reason=f"Blocked: requires mastery of {', '.join(blocking_desc)}.",
                    blocking_prerequisites=blocking_desc,
                    satisfied_prerequisites=satisfied_prereqs,
                )
                items.append(item)
                order_counter += 1
                continue

            # Case C: Unlocked & Unmastered -> Check Weekly Budget
            if allocated_minutes + duration <= student_budget:
                # Fits in budget -> Scheduled
                allocated_minutes += duration
                prereq_note = (
                    f"All prerequisites satisfied ({', '.join(satisfied_prereqs)})."
                    if satisfied_prereqs
                    else "Foundational topic (no prerequisites required)."
                )
                reason_text = (
                    f"Scheduled for this week: {prereq_note} "
                    f"Mastery ({round(score * 100)}%) is below {int(self.mastery_threshold * 100)}% threshold."
                )

                item = RoadmapItem(
                    topic=topic,
                    order=order_counter,
                    status=RoadmapStatus.SCHEDULED,
                    mastery_score=score,
                    mastery_level=level,
                    estimated_duration=duration,
                    is_unlocked=True,
                    reason=reason_text,
                    blocking_prerequisites=[],
                    satisfied_prerequisites=satisfied_prereqs,
                )
                items.append(item)
                order_counter += 1

                # The first scheduled topic becomes the next recommended topic
                if next_topic is None:
                    next_topic = item
            else:
                # Budget full -> Deferred to subsequent weeks
                item = RoadmapItem(
                    topic=topic,
                    order=order_counter,
                    status=RoadmapStatus.DEFERRED,
                    mastery_score=score,
                    mastery_level=level,
                    estimated_duration=duration,
                    is_unlocked=True,
                    reason=(
                        f"Deferred: Prerequisites satisfied, but adding {duration} min exceeds "
                        f"the available weekly budget ({student_budget - allocated_minutes} min remaining)."
                    ),
                    blocking_prerequisites=[],
                    satisfied_prerequisites=satisfied_prereqs,
                )
                items.append(item)
                order_counter += 1

        remaining_budget = max(0, student_budget - allocated_minutes)

        return RoadmapResult(
            user_id=uid,
            weekly_budget=student_budget,
            allocated_minutes=allocated_minutes,
            remaining_budget=remaining_budget,
            items=items,
            next_recommended_topic=next_topic,
        )

    def get_next_topic(
        self,
        user_id: Union[str, int],
        graph: Optional[ConceptGraph] = None,
        mastery_map: Optional[Dict[str, StudentMastery]] = None,
        time_budget: Optional[int] = None,
    ) -> Optional[RoadmapItem]:
        """Convenience method to retrieve only the next actionable topic."""
        roadmap = self.generate_roadmap(
            user_id=user_id,
            graph=graph,
            mastery_map=mastery_map,
            time_budget=time_budget,
        )
        return roadmap.next_recommended_topic
