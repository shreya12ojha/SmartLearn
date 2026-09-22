import sys
from pathlib import Path
_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

import unittest
from path_planning_agent.concept_graph import ConceptGraph, CycleDetectedError
from path_planning_agent.models import TopicNode


class TestConceptGraph(unittest.TestCase):

    def setUp(self):
        self.graph = ConceptGraph()
        self.t1 = TopicNode(id="loops", name="Loops", difficulty="Beginner", estimated_duration=30)
        self.t2 = TopicNode(id="arrays", name="Arrays", difficulty="Beginner", estimated_duration=30)
        self.t3 = TopicNode(id="recursion", name="Recursion", difficulty="Intermediate", estimated_duration=60)
        self.t4 = TopicNode(id="linked_lists", name="Linked Lists", difficulty="Intermediate", estimated_duration=60)
        self.t5 = TopicNode(id="trees", name="Trees", difficulty="Advanced", estimated_duration=90)

        for t in [self.t1, self.t2, self.t3, self.t4, self.t5]:
            self.graph.add_topic(t)

        # Edges:
        # Recursion requires Loops
        self.graph.add_prerequisite("recursion", "loops")
        # Linked Lists requires Arrays
        self.graph.add_prerequisite("linked_lists", "arrays")
        # Trees requires Recursion AND Linked Lists (multiple prerequisites)
        self.graph.add_prerequisite("trees", "recursion")
        self.graph.add_prerequisite("trees", "linked_lists")

    def test_topological_sort(self):
        sorted_topics = self.graph.topological_sort()
        self.assertEqual(len(sorted_topics), 5)
        indices = {t.id: idx for idx, t in enumerate(sorted_topics)}

        self.assertLess(indices["loops"], indices["recursion"])
        self.assertLess(indices["arrays"], indices["linked_lists"])
        self.assertLess(indices["recursion"], indices["trees"])
        self.assertLess(indices["linked_lists"], indices["trees"])

    def test_immediate_and_transitive_prerequisites(self):
        imm = self.graph.get_immediate_prerequisites("trees")
        self.assertCountEqual(imm, ["recursion", "linked_lists"])

        all_p = self.graph.get_all_prerequisites("trees")
        self.assertCountEqual(all_p, {"recursion", "linked_lists", "loops", "arrays"})

    def test_immediate_and_transitive_dependents(self):
        imm = self.graph.get_immediate_dependents("loops")
        self.assertCountEqual(imm, ["recursion"])

        all_d = self.graph.get_all_dependents("loops")
        self.assertCountEqual(all_d, {"recursion", "trees"})

    def test_cycle_detection(self):
        cyclic_graph = ConceptGraph()
        a = TopicNode(id="A", name="A")
        b = TopicNode(id="B", name="B")
        c = TopicNode(id="C", name="C")
        for node in [a, b, c]:
            cyclic_graph.add_topic(node)

        cyclic_graph.add_prerequisite("B", "A")  # A -> B
        cyclic_graph.add_prerequisite("C", "B")  # B -> C
        cyclic_graph.add_prerequisite("A", "C")  # C -> A (cycle!)

        self.assertTrue(cyclic_graph.has_cycle())
        with self.assertRaises(CycleDetectedError):
            cyclic_graph.topological_sort()

    def test_unlocking_logic(self):
        # Initial: no mastery
        mastery = {}
        self.assertTrue(self.graph.is_unlocked("loops", mastery, 0.75))
        self.assertTrue(self.graph.is_unlocked("arrays", mastery, 0.75))
        self.assertFalse(self.graph.is_unlocked("recursion", mastery, 0.75))
        self.assertFalse(self.graph.is_unlocked("trees", mastery, 0.75))

        # Pass Loops
        mastery["loops"] = 0.85
        self.assertTrue(self.graph.is_unlocked("recursion", mastery, 0.75))
        self.assertFalse(self.graph.is_unlocked("trees", mastery, 0.75))

        # Pass Recursion and Linked Lists
        mastery["recursion"] = 0.78
        mastery["arrays"] = 0.90
        mastery["linked_lists"] = 0.75
        self.assertTrue(self.graph.is_unlocked("trees", mastery, 0.75))


if __name__ == "__main__":
    unittest.main()
