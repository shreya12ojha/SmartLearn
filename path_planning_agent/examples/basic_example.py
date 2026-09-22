#!/usr/bin/env python3
"""
============================================================
PATH PLANNING AGENT DEMO
============================================================
A fully standalone demonstration of:
1. Concept Graph creation with multiple prerequisites
2. Student Mastery assessment ingestion
3. Path Planning Agent generating a personalized roadmap
4. Next Topic recommendation with prerequisite gating & weekly budget
5. Separate CMAB / LinUCB arm selection & feedback loop

Works with zero external dependencies and NO DATABASE_URL required.
"""

import math
import sys
from pathlib import Path
from typing import Dict, List

# Ensure package root is in python path when run directly
package_root = Path(__file__).resolve().parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from path_planning_agent.concept_graph import ConceptGraph
from path_planning_agent.models import (
    RoadmapStatus,
    StudentMastery,
    StudentProfile,
    TopicNode,
)
from path_planning_agent.planner import PathPlanningAgent
from path_planning_agent.providers import InMemoryProvider


# -------------------------------------------------------------
# Lightweight Standalone LinUCB Implementation for Demo
# -------------------------------------------------------------
class StandaloneLinUCB:
    """
    Standard LinUCB bandit for demonstration with zero external dependencies.
    Arms: video, text, practice, interactive.
    Context dimension: d = 7.
    """

    def __init__(self, arms: List[str], d: int = 7, alpha: float = 0.5):
        self.arms = arms
        self.d = d
        self.alpha = alpha
        # A_a = I_d, b_a = 0_d
        self.A: Dict[str, List[List[float]]] = {
            a: [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]
            for a in arms
        }
        self.b: Dict[str, List[float]] = {a: [0.0] * d for a in arms}

    def _invert_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """Gauss-Jordan elimination for matrix inversion."""
        n = len(matrix)
        augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]

        for i in range(n):
            # Pivot
            pivot = augmented[i][i]
            if abs(pivot) < 1e-9:
                for k in range(i + 1, n):
                    if abs(augmented[k][i]) > 1e-9:
                        augmented[i], augmented[k] = augmented[k], augmented[i]
                        pivot = augmented[i][i]
                        break
            for j in range(2 * n):
                augmented[i][j] /= pivot
            for k in range(n):
                if k != i:
                    factor = augmented[k][i]
                    for j in range(2 * n):
                        augmented[k][j] -= factor * augmented[i][j]

        return [row[n:] for row in augmented]

    def _dot(self, v1: List[float], v2: List[float]) -> float:
        return sum(x * y for x, y in zip(v1, v2))

    def _mat_vec(self, mat: List[List[float]], vec: List[float]) -> List[float]:
        return [self._dot(row, vec) for row in mat]

    def select_arm(self, x: List[float]) -> Dict[str, any]:
        best_arm = None
        highest_p = -float("inf")
        scores = {}

        for arm in self.arms:
            A_inv = self._invert_matrix(self.A[arm])
            theta = self._mat_vec(A_inv, self.b[arm])
            # Exploitation: theta^T * x
            mean = self._dot(theta, x)
            # Exploration: alpha * sqrt(x^T * A_inv * x)
            A_inv_x = self._mat_vec(A_inv, x)
            variance = max(0.0, self._dot(x, A_inv_x))
            bonus = self.alpha * math.sqrt(variance)
            p = mean + bonus

            scores[arm] = {"p": p, "mean": mean, "bonus": bonus}
            if p > highest_p:
                highest_p = p
                best_arm = arm

        return {
            "selected_arm": best_arm,
            "ucb_score": highest_p,
            "arm_scores": scores,
        }

    def update(self, arm: str, x: List[float], reward: float):
        # A_a += x * x^T
        for i in range(self.d):
            for j in range(self.d):
                self.A[arm][i][j] += x[i] * x[j]
        # b_a += reward * x
        for i in range(self.d):
            self.b[arm][i] += reward * x[i]


# -------------------------------------------------------------
# Main Demonstration Flow
# -------------------------------------------------------------
def main():
    print("============================================================")
    print("PATH PLANNING AGENT DEMO")
    print("============================================================\n")

    # 1. Build the Concept Graph
    print("[1] Building Concept Graph...")
    graph = ConceptGraph()

    t_arrays = TopicNode(id="arrays", name="Arrays", domain="DSA", difficulty="Beginner", estimated_duration=30)
    t_ll = TopicNode(id="linked_lists", name="Linked Lists", domain="DSA", difficulty="Intermediate", estimated_duration=60)
    t_rec = TopicNode(id="recursion", name="Recursion", domain="DSA", difficulty="Intermediate", estimated_duration=60)
    t_trees = TopicNode(id="trees", name="Trees", domain="DSA", difficulty="Advanced", estimated_duration=90)

    for topic in [t_arrays, t_ll, t_rec, t_trees]:
        graph.add_topic(topic)

    # Trees requires Linked Lists AND Recursion
    graph.add_prerequisite("linked_lists", "arrays")
    graph.add_prerequisite("trees", "linked_lists")
    graph.add_prerequisite("trees", "recursion")

    print(f"    Total Topics: {len(graph.get_all_topics())}")
    for t in graph.topological_sort():
        prereqs = graph.get_immediate_prerequisites(t.id)
        p_names = [graph.get_topic(p).name for p in prereqs]
        p_str = ", ".join(p_names) if p_names else "None (Foundational)"
        print(f"    - {t.name:<15} [Difficulty: {t.difficulty:<12} | Est: {t.get_duration()}m] <- Requires: {p_str}")

    # 2. Ingest Student Profile and Mastery
    print("\n[2] Ingesting Student Mastery & Profile...")
    student_id = "demo_student"
    weekly_budget = 180  # minutes

    provider = InMemoryProvider(graph=graph)
    provider.set_student_profile(
        StudentProfile(
            user_id=student_id,
            weekly_time_budget=weekly_budget,
            preferred_format="practice",
        )
    )

    # Mastery scores from prompt:
    # Arrays = 0.90, Linked Lists = 0.40, Recursion = 0.30, Trees = 0.10
    mastery_inputs = {
        "arrays": 0.90,
        "linked_lists": 0.40,
        "recursion": 0.30,
        "trees": 0.10,
    }
    for tid, score in mastery_inputs.items():
        provider.set_student_mastery(student_id, tid, score)
        t_name = graph.get_topic(tid).name
        status_label = "Mastered (>=75%)" if score >= 0.75 else "Needs Study (<75%)"
        print(f"    - {t_name:<15}: {score * 100:.1f}% -> {status_label}")

    # 3. Path Planning Execution
    print(f"\n[3] Executing Path Planning Agent (Weekly Budget: {weekly_budget} min, Threshold: 75%)...")
    agent = PathPlanningAgent(
        graph_provider=provider,
        mastery_provider=provider,
        context_provider=provider,
        mastery_threshold=0.75,
    )

    roadmap = agent.generate_roadmap(student_id)

    # 4. Display Roadmap
    print("\n============================================================")
    print("PERSONALIZED LEARNING ROADMAP")
    print("============================================================")
    print(f"Student ID       : {roadmap.user_id}")
    print(f"Weekly Budget    : {roadmap.weekly_budget} minutes")
    print(f"Allocated Time   : {roadmap.allocated_minutes} minutes")
    print(f"Remaining Budget : {roadmap.remaining_budget} minutes")
    print("------------------------------------------------------------")

    for item in roadmap.items:
        status_tag = f"[{item.status.value}]"
        print(f"{item.order}. {item.topic.name:<16} {status_tag:<12} (Mastery: {item.mastery_score * 100:.0f}%, Duration: {item.estimated_duration}m)")
        print(f"   Reason: {item.reason}")

    next_topic = roadmap.next_recommended_topic
    print("\n------------------------------------------------------------")
    if next_topic:
        print(f"NEXT RECOMMENDED TOPIC: {next_topic.topic.name} ({next_topic.topic.difficulty})")
        print(f"Action: Study {next_topic.topic.name} to build prerequisite mastery.")
    else:
        print("NEXT RECOMMENDED TOPIC: All topics mastered or no actionable topics.")
    print("------------------------------------------------------------\n")

    # 5. Demonstrate Separate CMAB / LinUCB Layer
    print("============================================================")
    print("SEPARATE CMAB / LINUCB RESOURCE RECOMMENDATION")
    print("============================================================")
    print("Question: 'How should the student study that topic?'")

    if next_topic:
        target_topic = next_topic.topic
        arms = ["video", "text", "practice", "interactive"]
        bandit = StandaloneLinUCB(arms=arms, d=7, alpha=0.5)

        # Context vector:
        # [current_mastery, norm_budget, pref_video, pref_text, pref_practice, pref_interactive, topic_diff]
        # Student prefers "practice"
        norm_budget = min(1.0, weekly_budget / 600.0)
        diff_val = 0.66 if target_topic.difficulty == "Intermediate" else 0.33
        context_x = [
            next_topic.mastery_score,  # 0.40
            norm_budget,               # 0.30
            0.0,                       # pref_video
            0.0,                       # pref_text
            1.0,                       # pref_practice
            0.0,                       # pref_interactive
            diff_val,                  # topic_diff
        ]

        print(f"\n1. Context Vector for {target_topic.name}:")
        print(f"   x = {context_x}")

        # LinUCB prediction before feedback
        pred = bandit.select_arm(context_x)
        print(f"\n2. LinUCB Arm Selection (Round 1):")
        for arm, s in pred["arm_scores"].items():
            print(f"   - {arm:<12}: UCB={s['p']:.4f} (Mean={s['mean']:.4f} + Bonus={s['bonus']:.4f})")
        print(f"   --> Recommended Learning Format: {pred['selected_arm'].upper()}")

        # Simulate student study & quiz feedback
        pre_mastery = next_topic.mastery_score  # 0.40
        post_mastery = 0.82  # Student completed interactive/practice quiz and scored 82%
        reward = post_mastery - pre_mastery
        print(f"\n3. Student Learning & Assessment:")
        print(f"   - Pre-Mastery  : {pre_mastery * 100:.1f}%")
        print(f"   - Post-Mastery : {post_mastery * 100:.1f}%")
        print(f"   - Reward       : {reward:+.3f} (Mastery Gain)")

        # Update LinUCB parameters
        bandit.update(pred["selected_arm"], context_x, reward)
        print(f"\n4. LinUCB Model Updated:")
        print(f"   - Arm '{pred['selected_arm']}' parameters updated with observation (x, reward={reward:+.3f}).")

        # Next prediction on updated model
        updated_pred = bandit.select_arm(context_x)
        print(f"\n5. LinUCB Arm Selection (Round 2 on Updated Model):")
        for arm, s in updated_pred["arm_scores"].items():
            print(f"   - {arm:<12}: UCB={s['p']:.4f} (Mean={s['mean']:.4f} + Bonus={s['bonus']:.4f})")
        print(f"   --> Next Recommendation: {updated_pred['selected_arm'].upper()}")

    print("\n============================================================")
    print("DEMO COMPLETE: ALL MODULE GOALS SUCCESSFULLY DEMONSTRATED")
    print("============================================================")


if __name__ == "__main__":
    main()
