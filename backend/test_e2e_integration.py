"""
============================================================
SMARTLEARN REAL END-TO-END INTEGRATION TEST SUITE
============================================================
Verifies the complete student lifecycle:
1. Registration & Authentication (JWT Token Generation)
2. Student Profile & Mastery State
3. Concept Graph & Prerequisite Topological Ordering
4. Personalized Roadmap Generation & Next Topic Recommendation
5. LinUCB Contextual Multi-Armed Bandit Resource Recommendation
6. Quiz Engine & Assessment Scoring
7. Authoritative Mastery Update in Database
8. Reward Calculation (post_mastery - pre_mastery)
9. Transaction-Safe LinUCB Bandit Parameter Update
10. Model Adaptation & Adaptive Next Topic Unlocking
11. Security & Authorization Enforcement (Cross-User Access Prevention)
"""

import os
import unittest

# Configure test environment variables before any application imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "e2e-super-secret-test-jwt-key-2026")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "120")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import (
    BanditInteraction,
    BanditModelState,
    Base,
    LearningResource,
    MasteryScore,
    QuizAttempt,
    QuizQuestion,
    Topic,
    TopicPrerequisite,
    User,
)

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestSmartLearnEndToEndIntegration(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)

        # -------------------------------------------------------------
        # Seed Realistic DSA Curriculum
        # Graph Structure:
        # Arrays (Beginner, 30m) -> Linked Lists (Intermediate, 60m)
        # Recursion (Intermediate, 60m)
        # Linked Lists + Recursion -> Trees (Advanced, 90m)
        # -------------------------------------------------------------
        self.t_arrays = Topic(name="Arrays", domain="DSA", difficulty_level="Beginner")
        self.t_ll = Topic(name="Linked Lists", domain="DSA", difficulty_level="Intermediate")
        self.t_rec = Topic(name="Recursion", domain="DSA", difficulty_level="Intermediate")
        self.t_trees = Topic(name="Trees", domain="DSA", difficulty_level="Advanced")

        self.db.add_all([self.t_arrays, self.t_ll, self.t_rec, self.t_trees])
        self.db.flush()

        # Prerequisites
        self.db.add(TopicPrerequisite(topic_id=self.t_ll.id, prerequisite_topic_id=self.t_arrays.id))
        self.db.add(TopicPrerequisite(topic_id=self.t_trees.id, prerequisite_topic_id=self.t_ll.id))
        self.db.add(TopicPrerequisite(topic_id=self.t_trees.id, prerequisite_topic_id=self.t_rec.id))

        # Learning resources for Linked Lists across all 4 formats
        self.res_ll_video = LearningResource(
            topic_id=self.t_ll.id,
            title="Linked Lists Visualized in 15 Minutes",
            url="https://youtube.com/watch?v=linked-lists-demo",
            format="video",
            estimated_time=30,
            difficulty="medium",
        )
        self.res_ll_practice = LearningResource(
            topic_id=self.t_ll.id,
            title="LeetCode: Reverse Linked List Hands-on Practice",
            url="https://leetcode.com/problems/reverse-linked-list/",
            format="practice",
            estimated_time=45,
            difficulty="medium",
        )
        self.res_ll_text = LearningResource(
            topic_id=self.t_ll.id,
            title="Comprehensive Guide to Singly and Doubly Linked Lists",
            url="https://example.com/ll-guide",
            format="text",
            estimated_time=25,
            difficulty="medium",
        )
        self.res_ll_interactive = LearningResource(
            topic_id=self.t_ll.id,
            title="VisuAlgo: Interactive Linked List Memory Pointer Simulator",
            url="https://visualgo.net/en/list",
            format="interactive",
            estimated_time=30,
            difficulty="medium",
        )
        self.db.add_all([self.res_ll_video, self.res_ll_practice, self.res_ll_text, self.res_ll_interactive])

        # Learning resources for Trees
        self.res_trees_practice = LearningResource(
            topic_id=self.t_trees.id,
            title="Binary Tree Traversals and Inversions",
            url="https://leetcode.com/problems/invert-binary-tree/",
            format="practice",
            estimated_time=60,
            difficulty="hard",
        )
        self.db.add(self.res_trees_practice)

        # Questions for Linked Lists
        self.q1 = QuizQuestion(
            topic_id=self.t_ll.id,
            question_text="What is the time complexity to insert a node at the head of a Singly Linked List?",
            options={"A": "O(1)", "B": "O(n)", "C": "O(log n)", "D": "O(n^2)"},
            correct_answer="A",
            difficulty="easy",
        )
        self.q2 = QuizQuestion(
            topic_id=self.t_ll.id,
            question_text="Which pointer technique is used to detect a cycle in a linked list?",
            options={"A": "Binary Search", "B": "Floyd's Tortoise and Hare (Two Pointers)", "C": "Greedy", "D": "DFS only"},
            correct_answer="B",
            difficulty="medium",
        )
        self.q3 = QuizQuestion(
            topic_id=self.t_ll.id,
            question_text="In a doubly linked list, deleting a node given its pointer requires traversing the list.",
            options={"A": "True, always", "B": "False, deletion takes O(1) time", "C": "Only if circular", "D": "Depends on language"},
            correct_answer="B",
            difficulty="hard",
        )
        self.db.add_all([self.q1, self.q2, self.q3])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_complete_end_to_end_student_lifecycle(self):
        # =============================================================
        # 1. Registration & Authentication
        # =============================================================
        signup_res = self.client.post(
            "/api/auth/signup",
            json={
                "name": "Sarah Student",
                "email": "sarah.student@smartlearn.ai",
                "password": "Password123!",
            },
        )
        self.assertEqual(signup_res.status_code, 200)
        auth_data = signup_res.json()
        user_id = auth_data["user_id"]
        token = auth_data["token"]
        self.assertIsNotNone(token)
        headers = {"Authorization": f"Bearer {token}"}

        # Verify Login endpoint also works
        login_res = self.client.post(
            "/api/auth/login",
            json={
                "email": "sarah.student@smartlearn.ai",
                "password": "Password123!",
            },
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["user_id"], user_id)

        # Update student time budget and preferred format in DB
        user = self.db.query(User).filter(User.id == user_id).first()
        user.weekly_time_budget = 180  # 180 minutes available
        user.preferred_format = "practice"
        self.db.commit()

        # =============================================================
        # 2. Set Initial Student Mastery
        # - Arrays = 0.90 (>= 0.75 -> Mastered)
        # - Recursion = 0.80 (>= 0.75 -> Mastered)
        # - Linked Lists = 0.35 (< 0.75 -> Unmastered, Unlocked because Arrays is Mastered)
        # - Trees = 0.10 (Blocked because Linked Lists is below 0.75)
        # =============================================================
        self.db.add(MasteryScore(user_id=user_id, topic_id=self.t_arrays.id, mastery_score=0.90, mastery_level="Advanced"))
        self.db.add(MasteryScore(user_id=user_id, topic_id=self.t_rec.id, mastery_score=0.80, mastery_level="Advanced"))
        self.db.add(MasteryScore(user_id=user_id, topic_id=self.t_ll.id, mastery_score=0.35, mastery_level="Beginner"))
        self.db.add(MasteryScore(user_id=user_id, topic_id=self.t_trees.id, mastery_score=0.10, mastery_level="Beginner"))
        self.db.commit()

        # =============================================================
        # 3. Path Planning: Generate Personalized Roadmap
        # =============================================================
        rm_res = self.client.get(f"/api/path-planning/roadmap/{user_id}", headers=headers)
        self.assertEqual(rm_res.status_code, 200)
        roadmap_data = rm_res.json()

        self.assertEqual(roadmap_data["user_id"], user_id)
        self.assertEqual(roadmap_data["weekly_budget"], 180)
        self.assertEqual(roadmap_data["allocated_minutes"], 60)  # Linked Lists (60m) scheduled
        self.assertEqual(roadmap_data["remaining_budget"], 120)

        # Inspect Topic Statuses
        status_map = {item["topic_name"]: item["status"] for item in roadmap_data["roadmap"]}
        self.assertEqual(status_map["Arrays"], "MASTERED")
        self.assertEqual(status_map["Recursion"], "MASTERED")
        self.assertEqual(status_map["Linked Lists"], "SCHEDULED")
        self.assertEqual(status_map["Trees"], "BLOCKED")

        # Verify next recommended topic
        self.assertIsNotNone(roadmap_data["next_topic"])
        self.assertEqual(roadmap_data["next_topic"]["topic_name"], "Linked Lists")

        # =============================================================
        # 4. Path Planning: Query Next Topic Endpoint
        # =============================================================
        nxt_res = self.client.get(f"/api/path-planning/next-topic/{user_id}", headers=headers)
        self.assertEqual(nxt_res.status_code, 200)
        nxt_data = nxt_res.json()
        self.assertIsNotNone(nxt_data["next_topic"])
        self.assertEqual(nxt_data["next_topic"]["topic_name"], "Linked Lists")
        target_topic_id = nxt_data["next_topic"]["topic_id"]

        # =============================================================
        # 5. CMAB / LinUCB: Get Resource Recommendation for Next Topic
        # =============================================================
        rec_res = self.client.get(
            f"/api/recommendations/resource?user_id={user_id}&topic_id={target_topic_id}",
            headers=headers,
        )
        self.assertEqual(rec_res.status_code, 200)
        rec_data = rec_res.json()

        selected_arm = rec_data["selected_arm"]
        self.assertIn(selected_arm, ["video", "text", "practice", "interactive"])
        self.assertIsNotNone(rec_data["resource"])
        self.assertGreater(rec_data["ucb_score"], 0.0)
        self.assertGreater(rec_data["exploration_bonus"], 0.0)

        # Verify interaction recorded in DB
        interaction = (
            self.db.query(BanditInteraction)
            .filter(BanditInteraction.user_id == user_id, BanditInteraction.topic_id == target_topic_id)
            .first()
        )
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.selected_arm, selected_arm)
        self.assertAlmostEqual(interaction.pre_mastery, 0.35, places=2)

        # =============================================================
        # 6. Student Takes Quiz: Fetch Questions & Submit Answers
        # =============================================================
        q_res = self.client.get(f"/api/quiz?topic={target_topic_id}")
        self.assertEqual(q_res.status_code, 200)
        questions = q_res.json()["questions"]
        self.assertEqual(len(questions), 3)

        # Submit all 3 questions correctly
        submit_payload = {
            "user_id": user_id,
            "quiz_type": "checkpoint",
            "answers": [
                {"question_id": self.q1.id, "selected_option": "A"},
                {"question_id": self.q2.id, "selected_option": "B"},
                {"question_id": self.q3.id, "selected_option": "B"},
            ],
        }
        sub_res = self.client.post("/api/quiz/submit", json=submit_payload)
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.json()

        # Verify mastery score updated in assessment response
        self.assertIn("mastery", sub_data)
        post_mastery = sub_data["mastery"][str(target_topic_id)]
        self.assertAlmostEqual(post_mastery, 1.00, places=2)

        # Verify detailed question review returned
        self.assertIn("results", sub_data)
        self.assertEqual(len(sub_data["results"]), 3)
        self.assertTrue(all(r["is_correct"] for r in sub_data["results"]))

        # Verify database state was updated
        db_mastery = (
            self.db.query(MasteryScore)
            .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id == target_topic_id)
            .first()
        )
        self.assertAlmostEqual(db_mastery.mastery_score, 1.00, places=2)
        self.assertEqual(db_mastery.mastery_level, "Advanced")

        db_attempt = (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.topic_id == target_topic_id)
            .first()
        )
        self.assertIsNotNone(db_attempt)
        self.assertAlmostEqual(db_attempt.score, 1.00, places=2)

        # =============================================================
        # 7. CMAB Feedback: Compute Reward & Update LinUCB Model
        # Authoritative Reward = post_mastery - pre_mastery
        # =============================================================
        pre_mastery = 0.35
        expected_reward = round(post_mastery - pre_mastery, 3)  # +0.650
        self.assertAlmostEqual(expected_reward, 0.65, places=2)

        fb_payload = {
            "user_id": user_id,
            "topic_id": target_topic_id,
            "selected_arm": selected_arm,
            "pre_mastery": pre_mastery,
            "post_mastery": post_mastery,
        }
        fb_res = self.client.post("/api/recommendations/feedback", json=fb_payload, headers=headers)
        self.assertEqual(fb_res.status_code, 200)
        fb_data = fb_res.json()

        self.assertEqual(fb_data["status"], "success")
        self.assertAlmostEqual(fb_data["reward"], expected_reward, places=2)
        self.assertEqual(fb_data["arm"], selected_arm)

        # Verify BanditModelState persisted in database with row locking
        arm_model = (
            self.db.query(BanditModelState)
            .filter(BanditModelState.arm_name == selected_arm)
            .first()
        )
        self.assertIsNotNone(arm_model)
        # Vector b must have accumulated positive values from reward * x
        self.assertGreater(sum(arm_model.b_vector), 0.0)

        # =============================================================
        # 8. Adaptive Regeneration: Subsequent Recommendation & Roadmap Unlocking
        # Now Linked Lists is MASTERED (1.00 >= 0.75).
        # Since Linked Lists (1.0) and Recursion (0.80) are both >= 0.75,
        # TREES SHOULD NOW BE UNLOCKED AND SCHEDULED!
        # =============================================================
        updated_rm_res = self.client.get(f"/api/path-planning/roadmap/{user_id}", headers=headers)
        self.assertEqual(updated_rm_res.status_code, 200)
        updated_rm_data = updated_rm_res.json()

        updated_status_map = {item["topic_name"]: item["status"] for item in updated_rm_data["roadmap"]}
        self.assertEqual(updated_status_map["Arrays"], "MASTERED")
        self.assertEqual(updated_status_map["Recursion"], "MASTERED")
        self.assertEqual(updated_status_map["Linked Lists"], "MASTERED")
        # TREES IS UNLOCKED!
        self.assertEqual(updated_status_map["Trees"], "SCHEDULED")

        # Next topic is now Trees!
        self.assertIsNotNone(updated_rm_data["next_topic"])
        self.assertEqual(updated_rm_data["next_topic"]["topic_name"], "Trees")

        # =============================================================
        # 9. Security & Authorization Enforcement
        # Verify that authenticated Sarah cannot access or modify user 999
        # =============================================================
        rogue_rm = self.client.get("/api/path-planning/roadmap/999", headers=headers)
        self.assertEqual(rogue_rm.status_code, 403)

        rogue_next = self.client.get("/api/path-planning/next-topic/999", headers=headers)
        self.assertEqual(rogue_next.status_code, 403)

        rogue_rec = self.client.get(f"/api/recommendations/resource?user_id=999&topic_id={self.t_ll.id}", headers=headers)
        self.assertEqual(rogue_rec.status_code, 403)

        rogue_fb = self.client.post(
            "/api/recommendations/feedback",
            json={
                "user_id": 999,
                "topic_id": self.t_ll.id,
                "selected_arm": "practice",
                "pre_mastery": 0.2,
                "post_mastery": 0.8,
            },
            headers=headers,
        )
        self.assertEqual(rogue_fb.status_code, 403)


if __name__ == "__main__":
    unittest.main()
