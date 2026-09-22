import os
import unittest

# Ensure test environment variables are set before app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-12345")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


from app.models import (
    Base,
    LearningResource,
    MasteryScore,
    Topic,
    TopicPrerequisite,
    User,
)
from app.cmab import LinUCBBanditService, build_context_vector
from app.path_planning_agent import (
    SQLAlchemyConceptGraphProvider,
    SQLAlchemyMasteryProvider,
    SQLAlchemyStudentContextProvider,
    get_student_next_topic,
    get_student_roadmap,
)
from app.main import app
from app.database import get_db

# Setup test DB using StaticPool so in-memory DB is shared across threads
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
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


class TestBackendPathPlanningAndCMAB(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        # 1. Create User
        self.user = User(
            name="Alice",
            email="alice@example.com",
            hashed_password="fakehashpassword123",
            weekly_time_budget=180,
            preferred_format="practice",
        )
        self.db.add(self.user)
        self.db.flush()

        # 2. Create Topics
        self.t_arrays = Topic(name="Arrays", domain="DSA", difficulty_level="Beginner")
        self.t_ll = Topic(name="Linked Lists", domain="DSA", difficulty_level="Intermediate")
        self.t_rec = Topic(name="Recursion", domain="DSA", difficulty_level="Intermediate")
        self.t_trees = Topic(name="Trees", domain="DSA", difficulty_level="Advanced")

        for t in [self.t_arrays, self.t_ll, self.t_rec, self.t_trees]:
            self.db.add(t)
        self.db.flush()

        # 3. Prerequisites:
        # Linked Lists -> Arrays
        self.db.add(TopicPrerequisite(topic_id=self.t_ll.id, prerequisite_topic_id=self.t_arrays.id))
        # Trees -> Linked Lists
        self.db.add(TopicPrerequisite(topic_id=self.t_trees.id, prerequisite_topic_id=self.t_ll.id))
        # Trees -> Recursion
        self.db.add(TopicPrerequisite(topic_id=self.t_trees.id, prerequisite_topic_id=self.t_rec.id))

        # 4. Learning Resources
        self.res_ll_practice = LearningResource(
            topic_id=self.t_ll.id,
            title="Interactive Linked Lists",
            url="https://example.com/ll-practice",
            format="practice",
            estimated_time=60,
            difficulty="medium",
        )
        self.res_ll_video = LearningResource(
            topic_id=self.t_ll.id,
            title="Linked Lists Video Tutorial",
            url="https://example.com/ll-video",
            format="video",
            estimated_time=60,
            difficulty="medium",
        )
        self.db.add(self.res_ll_practice)
        self.db.add(self.res_ll_video)

        # 5. Mastery Scores
        # Arrays = 0.90 (Mastered)
        self.db.add(MasteryScore(user_id=self.user.id, topic_id=self.t_arrays.id, mastery_score=0.90, mastery_level="Advanced"))
        # Linked Lists = 0.40 (Needs Study)
        self.db.add(MasteryScore(user_id=self.user.id, topic_id=self.t_ll.id, mastery_score=0.40, mastery_level="Intermediate"))
        # Recursion = 0.30 (Needs Study)
        self.db.add(MasteryScore(user_id=self.user.id, topic_id=self.t_rec.id, mastery_score=0.30, mastery_level="Beginner"))
        # Trees = 0.10 (Blocked)
        self.db.add(MasteryScore(user_id=self.user.id, topic_id=self.t_trees.id, mastery_score=0.10, mastery_level="Beginner"))

        self.db.commit()
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_sqlalchemy_providers_and_roadmap(self):
        roadmap = get_student_roadmap(self.db, self.user.id)

        self.assertEqual(roadmap.user_id, self.user.id)
        self.assertEqual(roadmap.weekly_budget, 180)
        self.assertEqual(roadmap.allocated_minutes, 120)  # Linked Lists (60m) + Recursion (60m)

        status_by_name = {item.topic_name: item.status for item in roadmap.roadmap}
        self.assertEqual(status_by_name["Arrays"], "MASTERED")
        self.assertEqual(status_by_name["Linked Lists"], "SCHEDULED")
        self.assertEqual(status_by_name["Recursion"], "SCHEDULED")
        self.assertEqual(status_by_name["Trees"], "BLOCKED")

        self.assertIsNotNone(roadmap.next_topic)
        self.assertIn(roadmap.next_topic.topic_name, ["Linked Lists", "Recursion"])

    def test_cmab_linucb_recommend_and_update(self):
        bandit = LinUCBBanditService(alpha=0.5)

        # Recommend resource for Linked Lists
        rec = bandit.recommend_resource_format(
            db=self.db,
            user=self.user,
            topic=self.t_ll,
            current_mastery=0.40,
        )

        self.assertEqual(rec["topic_id"], self.t_ll.id)
        self.assertIn(rec["selected_arm"], ["video", "text", "practice", "interactive"])
        self.assertIsNotNone(rec["resource"])

        # Update model with post-quiz feedback
        result = bandit.update_model(
            db=self.db,
            user_id=self.user.id,
            topic_id=self.t_ll.id,
            selected_arm=rec["selected_arm"],
            pre_mastery=0.40,
            post_mastery=0.85,
        )

        self.assertEqual(result["status"], "updated")
        self.assertAlmostEqual(result["reward"], 0.45, places=3)

    def test_api_endpoints(self):
        # 1. Test GET /api/path-planning/roadmap/{user_id}
        res_rm = self.client.get(f"/api/path-planning/roadmap/{self.user.id}")
        self.assertEqual(res_rm.status_code, 200)
        data = res_rm.json()
        self.assertEqual(data["user_id"], self.user.id)
        self.assertEqual(data["weekly_budget"], 180)
        self.assertIn("roadmap", data)
        self.assertIn("next_topic", data)

        # 2. Test GET /api/path-planning/next-topic/{user_id}
        res_nxt = self.client.get(f"/api/path-planning/next-topic/{self.user.id}")
        self.assertEqual(res_nxt.status_code, 200)
        data_nxt = res_nxt.json()
        self.assertIsNotNone(data_nxt["next_topic"])

        # 3. Test GET /api/recommendations/resource
        res_rec = self.client.get(f"/api/recommendations/resource?user_id={self.user.id}&topic_id={self.t_ll.id}")
        self.assertEqual(res_rec.status_code, 200)
        data_rec = res_rec.json()
        self.assertEqual(data_rec["topic_id"], self.t_ll.id)
        self.assertIn(data_rec["selected_arm"], ["video", "text", "practice", "interactive"])

        # 4. Test POST /api/recommendations/feedback
        payload = {
            "user_id": self.user.id,
            "topic_id": self.t_ll.id,
            "selected_arm": data_rec["selected_arm"],
            "pre_mastery": 0.40,
            "post_mastery": 0.85,
        }
        res_fb = self.client.post("/api/recommendations/feedback", json=payload)
        self.assertEqual(res_fb.status_code, 200)
        data_fb = res_fb.json()
        self.assertEqual(data_fb["status"], "success")
        self.assertAlmostEqual(data_fb["reward"], 0.45, places=3)

        # 5. Test GET /api/resources
        res_list = self.client.get(f"/api/resources?topic_id={self.t_ll.id}")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 2)


if __name__ == "__main__":
    unittest.main()
