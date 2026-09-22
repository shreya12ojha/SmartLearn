import sys
from pathlib import Path
_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

import unittest
from path_planning_agent.concept_graph import ConceptGraph
from path_planning_agent.models import (
    RoadmapStatus,
    StudentMastery,
    StudentProfile,
    TopicNode,
)
from path_planning_agent.planner import PathPlanningAgent
from path_planning_agent.providers import InMemoryProvider


class TestPathPlanningAgent(unittest.TestCase):

    def setUp(self):
        self.graph = ConceptGraph()
        # Create topics with explicit durations
        self.t_arrays = TopicNode(id="arrays", name="Arrays", difficulty="Beginner", estimated_duration=30)
        self.t_ll = TopicNode(id="linked_lists", name="Linked Lists", difficulty="Intermediate", estimated_duration=60)
        self.t_rec = TopicNode(id="recursion", name="Recursion", difficulty="Intermediate", estimated_duration=60)
        self.t_trees = TopicNode(id="trees", name="Trees", difficulty="Advanced", estimated_duration=90)

        for t in [self.t_arrays, self.t_ll, self.t_rec, self.t_trees]:
            self.graph.add_topic(t)

        # Edges:
        # Linked Lists requires Arrays
        self.graph.add_prerequisite("linked_lists", "arrays")
        # Trees requires BOTH Linked Lists AND Recursion
        self.graph.add_prerequisite("trees", "linked_lists")
        self.graph.add_prerequisite("trees", "recursion")

        self.provider = InMemoryProvider(graph=self.graph)
        self.agent = PathPlanningAgent(
            graph_provider=self.provider,
            mastery_provider=self.provider,
            context_provider=self.provider,
            mastery_threshold=0.75,
        )

    def test_deterministic_example_scenario(self):
        """
        Tests the user prompt's deterministic scenario:
        Arrays = 0.90 (Mastered)
        Linked Lists = 0.40 (Unlocked, Unmastered)
        Recursion = 0.30 (Unlocked, Unmastered)
        Trees = 0.10 (Blocked: requires Linked Lists and Recursion >= 0.75)
        Weekly budget: 180 minutes.
        """
        user_id = "demo_student"
        self.provider.set_student_profile(
            StudentProfile(user_id=user_id, weekly_time_budget=180, preferred_format="practice")
        )
        self.provider.set_student_mastery(user_id, "arrays", 0.90, "Advanced")
        self.provider.set_student_mastery(user_id, "linked_lists", 0.40, "Intermediate")
        self.provider.set_student_mastery(user_id, "recursion", 0.30, "Beginner")
        self.provider.set_student_mastery(user_id, "trees", 0.10, "Beginner")

        roadmap = self.agent.generate_roadmap(user_id)

        # Verify budget allocation
        self.assertEqual(roadmap.weekly_budget, 180)
        # Linked Lists (60m) + Recursion (60m) = 120m scheduled.
        self.assertEqual(roadmap.allocated_minutes, 120)
        self.assertEqual(roadmap.remaining_budget, 60)

        item_map = {item.topic.id: item for item in roadmap.items}

        # Arrays should be MASTERED
        self.assertEqual(item_map["arrays"].status, RoadmapStatus.MASTERED)
        self.assertTrue(item_map["arrays"].is_unlocked)

        # Linked Lists should be SCHEDULED
        self.assertEqual(item_map["linked_lists"].status, RoadmapStatus.SCHEDULED)
        self.assertTrue(item_map["linked_lists"].is_unlocked)

        # Recursion should be SCHEDULED
        self.assertEqual(item_map["recursion"].status, RoadmapStatus.SCHEDULED)
        self.assertTrue(item_map["recursion"].is_unlocked)

        # Trees should be BLOCKED because both Linked Lists and Recursion < 0.75
        self.assertEqual(item_map["trees"].status, RoadmapStatus.BLOCKED)
        self.assertFalse(item_map["trees"].is_unlocked)
        self.assertIn("Linked Lists", item_map["trees"].reason)
        self.assertIn("Recursion", item_map["trees"].reason)

        # Next recommended topic should be the first unmastered scheduled topic
        self.assertIsNotNone(roadmap.next_recommended_topic)
        self.assertIn(roadmap.next_recommended_topic.topic.id, ["linked_lists", "recursion"])

    def test_budget_exhaustion_defers_topics(self):
        """When budget is small, unlocked topics that exceed budget should be DEFERRED."""
        user_id = "low_budget_student"
        # Budget is only 60 minutes
        self.provider.set_student_profile(
            StudentProfile(user_id=user_id, weekly_time_budget=60)
        )
        self.provider.set_student_mastery(user_id, "arrays", 0.90, "Advanced")
        self.provider.set_student_mastery(user_id, "linked_lists", 0.20, "Beginner")
        self.provider.set_student_mastery(user_id, "recursion", 0.20, "Beginner")

        roadmap = self.agent.generate_roadmap(user_id)

        scheduled = roadmap.scheduled_items
        deferred = roadmap.deferred_items

        # One 60-min topic gets scheduled, the other gets deferred
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(len(deferred), 1)
        self.assertEqual(roadmap.allocated_minutes, 60)
        self.assertEqual(roadmap.remaining_budget, 0)
        self.assertEqual(deferred[0].status, RoadmapStatus.DEFERRED)

    def test_unassessed_topic_treated_as_zero_mastery(self):
        user_id = "new_student"
        self.provider.set_student_profile(
            StudentProfile(user_id=user_id, weekly_time_budget=300)
        )
        # No mastery data at all
        roadmap = self.agent.generate_roadmap(user_id)

        # Arrays and Recursion have no prereqs, so both should be scheduled
        item_map = {item.topic.id: item for item in roadmap.items}
        self.assertEqual(item_map["arrays"].status, RoadmapStatus.SCHEDULED)
        self.assertEqual(item_map["arrays"].mastery_level, "Unassessed")
        self.assertEqual(item_map["recursion"].status, RoadmapStatus.SCHEDULED)
        # Linked Lists requires Arrays (which is 0.0), so it should be BLOCKED
        self.assertEqual(item_map["linked_lists"].status, RoadmapStatus.BLOCKED)
        # Trees requires Linked Lists and Recursion, so BLOCKED
        self.assertEqual(item_map["trees"].status, RoadmapStatus.BLOCKED)


if __name__ == "__main__":
    unittest.main()
