import logging
import math
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import BanditInteraction, BanditModelState, LearningResource, Topic, User

logger = logging.getLogger(__name__)

SUPPORTED_ARMS = ["video", "text", "practice", "interactive"]
CONTEXT_DIMENSION = 7
DEFAULT_ALPHA = 0.5


def build_context_vector(
    current_mastery: float,
    weekly_budget: int,
    preferred_format: str,
    difficulty_level: str,
) -> Tuple[List[float], Dict[str, float]]:
    """
    Constructs the normalized 7-dimensional context vector:
    1. current_mastery (0.0 to 1.0)
    2. normalized_budget (budget / 600.0 clamped to [0, 1])
    3. is_pref_video (1.0 or 0.0)
    4. is_pref_text (1.0 or 0.0)
    5. is_pref_practice (1.0 or 0.0)
    6. is_pref_interactive (1.0 or 0.0)
    7. topic_difficulty (Beginner=0.33, Intermediate=0.66, Advanced=1.0)
    """
    c_mastery = max(0.0, min(1.0, float(current_mastery)))
    norm_budget = max(0.0, min(1.0, float(weekly_budget) / 600.0))

    pref = (preferred_format or "").strip().lower()
    is_video = 1.0 if pref == "video" else 0.0
    is_text = 1.0 if pref == "text" else 0.0
    is_practice = 1.0 if pref == "practice" else 0.0
    is_interactive = 1.0 if pref == "interactive" else 0.0

    diff = (difficulty_level or "").strip().lower()
    if diff == "advanced":
        topic_diff = 1.0
    elif diff == "intermediate":
        topic_diff = 0.66
    else:
        topic_diff = 0.33

    features = [
        c_mastery,
        norm_budget,
        is_video,
        is_text,
        is_practice,
        is_interactive,
        topic_diff,
    ]

    feature_dict = {
        "current_mastery": c_mastery,
        "normalized_budget": norm_budget,
        "is_pref_video": is_video,
        "is_pref_text": is_text,
        "is_pref_practice": is_practice,
        "is_pref_interactive": is_interactive,
        "topic_difficulty": topic_diff,
    }

    return features, feature_dict


def invert_matrix_7x7(matrix: List[List[float]]) -> List[List[float]]:
    """
    Pure Python Gauss-Jordan elimination for inverting a 7x7 matrix.
    Safe and robust with zero external library requirements.
    """
    n = len(matrix)
    augmented = [
        row[:] + [1.0 if i == j else 0.0 for j in range(n)]
        for i, row in enumerate(matrix)
    ]

    for i in range(n):
        # Pivot search
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


def dot_product(v1: List[float], v2: List[float]) -> float:
    return sum(x * y for x, y in zip(v1, v2))


def mat_vec_multiply(mat: List[List[float]], vec: List[float]) -> List[float]:
    return [dot_product(row, vec) for row in mat]


class LinUCBBanditService:
    """
    Production Contextual Multi-Armed Bandit using LinUCB.
    Features:
    - 4 Arms (video, text, practice, interactive)
    - 7-dim context vector
    - Transaction-safe database persistence with row locking
    - In-memory caching for low latency
    """

    def __init__(self, alpha: float = DEFAULT_ALPHA):
        self.arms = SUPPORTED_ARMS
        self.d = CONTEXT_DIMENSION
        self.alpha = alpha

        # In-memory cache: arm_name -> (A_matrix, b_vector)
        self._cache_A: Dict[str, List[List[float]]] = {}
        self._cache_b: Dict[str, List[float]] = {}
        self._init_defaults()

    def _init_defaults(self):
        for arm in self.arms:
            self._cache_A[arm] = [
                [1.0 if i == j else 0.0 for j in range(self.d)]
                for i in range(self.d)
            ]
            self._cache_b[arm] = [0.0] * self.d

    def _load_arm_state(self, db: Session, arm: str, for_update: bool = False) -> Tuple[List[List[float]], List[float]]:
        """
        Loads the arm's A matrix and b vector from DB.
        If for_update=True, applies row-level locking (SELECT ... FOR UPDATE)
        to prevent lost updates across concurrent workers.
        """
        query = db.query(BanditModelState).filter(BanditModelState.arm_name == arm)
        if for_update:
            try:
                query = query.with_for_update()
            except Exception:
                # Some dialects (like SQLite in tests) may not support FOR UPDATE
                pass

        row = query.first()
        if row:
            return row.A_matrix, row.b_vector

        # If not present in DB, initialize new row
        init_A = [[1.0 if i == j else 0.0 for j in range(self.d)] for i in range(self.d)]
        init_b = [0.0] * self.d
        new_row = BanditModelState(
            arm_name=arm,
            A_matrix=init_A,
            b_vector=init_b,
        )
        db.add(new_row)
        try:
            db.commit()
            db.refresh(new_row)
        except Exception:
            db.rollback()
            row = db.query(BanditModelState).filter(BanditModelState.arm_name == arm).first()
            if row:
                return row.A_matrix, row.b_vector

        return init_A, init_b

    def recommend_resource_format(
        self, db: Session, user: User, topic: Topic, current_mastery: float
    ) -> Dict[str, any]:
        """
        Calculates LinUCB score for each arm and selects the optimal format.
        Also retrieves the best matching LearningResource from the database.
        """
        x, feature_dict = build_context_vector(
            current_mastery=current_mastery,
            weekly_budget=user.weekly_time_budget or 300,
            preferred_format=user.preferred_format or "video",
            difficulty_level=topic.difficulty_level or "Beginner",
        )

        best_arm = None
        highest_p = -float("inf")
        best_bonus = 0.0
        arm_stats = {}

        for arm in self.arms:
            A_mat, b_vec = self._load_arm_state(db, arm, for_update=False)
            A_inv = invert_matrix_7x7(A_mat)
            theta = mat_vec_multiply(A_inv, b_vec)

            # Exploitation: theta^T * x
            mean = dot_product(theta, x)
            # Exploration: alpha * sqrt(x^T * A_inv * x)
            A_inv_x = mat_vec_multiply(A_inv, x)
            variance = max(0.0, dot_product(x, A_inv_x))
            bonus = self.alpha * math.sqrt(variance)
            p = mean + bonus

            arm_stats[arm] = {"p": p, "mean": mean, "bonus": bonus}
            if p > highest_p:
                highest_p = p
                best_arm = arm
                best_bonus = bonus

        # Retrieve a matching learning resource from DB for this topic and arm
        resource = (
            db.query(LearningResource)
            .filter(LearningResource.topic_id == topic.id, LearningResource.format == best_arm)
            .first()
        )
        # Fallback: any resource for this topic if preferred format is missing
        if not resource:
            resource = (
                db.query(LearningResource)
                .filter(LearningResource.topic_id == topic.id)
                .first()
            )

        # Record initial pending interaction in DB
        interaction = BanditInteraction(
            user_id=user.id,
            topic_id=topic.id,
            selected_arm=best_arm,
            context=x,
            pre_mastery=current_mastery,
            post_mastery=None,
            reward=None,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "selected_arm": best_arm,
            "resource": resource,
            "ucb_score": highest_p,
            "exploration_bonus": best_bonus,
            "context_features": feature_dict,
            "arm_stats": arm_stats,
            "interaction_id": interaction.id,
        }

    def update_model(
        self,
        db: Session,
        user_id: int,
        topic_id: int,
        selected_arm: str,
        pre_mastery: float,
        post_mastery: float,
        interaction_id: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Updates LinUCB parameters with row-level transaction safety:
        A_a += x * x^T
        b_a += reward * x
        reward = post_mastery - pre_mastery
        """
        if selected_arm not in self.arms:
            raise ValueError(f"Unknown arm: {selected_arm}")

        reward = max(-1.0, min(1.0, float(post_mastery - pre_mastery)))

        # Load user and topic to rebuild exact context x
        user = db.query(User).filter(User.id == user_id).first()
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not user or not topic:
            raise ValueError("User or Topic not found for bandit update")

        x, _ = build_context_vector(
            current_mastery=pre_mastery,
            weekly_budget=user.weekly_time_budget or 300,
            preferred_format=user.preferred_format or "video",
            difficulty_level=topic.difficulty_level or "Beginner",
        )

        # 1. Acquire DB lock on arm row for concurrency safety
        row = (
            db.query(BanditModelState)
            .filter(BanditModelState.arm_name == selected_arm)
            .with_for_update()
            .first()
        )
        if not row:
            A_mat = [[1.0 if i == j else 0.0 for j in range(self.d)] for i in range(self.d)]
            b_vec = [0.0] * self.d
            row = BanditModelState(arm_name=selected_arm, A_matrix=A_mat, b_vector=b_vec)
            db.add(row)
            db.flush()
        else:
            A_mat = [r[:] for r in row.A_matrix]
            b_vec = row.b_vector[:]

        # 2. Update A_a += x * x^T
        for i in range(self.d):
            for j in range(self.d):
                A_mat[i][j] += x[i] * x[j]

        # 3. Update b_a += reward * x
        for i in range(self.d):
            b_vec[i] += reward * x[i]

        row.A_matrix = A_mat
        row.b_vector = b_vec

        # 4. Update or insert BanditInteraction
        if interaction_id:
            interaction = db.query(BanditInteraction).filter(BanditInteraction.id == interaction_id).first()
            if interaction:
                interaction.post_mastery = post_mastery
                interaction.reward = reward
        else:
            # Find latest uncompleted interaction for this user, topic, and arm
            latest_interaction = (
                db.query(BanditInteraction)
                .filter(
                    BanditInteraction.user_id == user_id,
                    BanditInteraction.topic_id == topic_id,
                    BanditInteraction.selected_arm == selected_arm,
                    BanditInteraction.reward.is_(None),
                )
                .order_by(BanditInteraction.timestamp.desc())
                .first()
            )
            if latest_interaction:
                latest_interaction.post_mastery = post_mastery
                latest_interaction.reward = reward
            else:
                db.add(
                    BanditInteraction(
                        user_id=user_id,
                        topic_id=topic_id,
                        selected_arm=selected_arm,
                        context=x,
                        pre_mastery=pre_mastery,
                        post_mastery=post_mastery,
                        reward=reward,
                    )
                )

        db.commit()

        # Update in-memory cache
        self._cache_A[selected_arm] = A_mat
        self._cache_b[selected_arm] = b_vec

        return {
            "arm": selected_arm,
            "reward": reward,
            "pre_mastery": pre_mastery,
            "post_mastery": post_mastery,
            "status": "updated",
        }


# Global service instance
bandit_service = LinUCBBanditService()
