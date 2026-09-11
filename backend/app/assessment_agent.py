from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime

from app.models import QuizQuestion, QuizAttempt, MasteryScore

DIFFICULTY_WEIGHTS = {"easy": 1, "medium": 2, "hard": 3}


def classify_mastery_level(score: float) -> str:
    if score < 0.4:
        return "Beginner"
    elif score < 0.75:
        return "Intermediate"
    else:
        return "Advanced"


def score_quiz(db: Session, user_id: int, answers: list) -> dict:
    """
    Takes raw answers, computes a weighted mastery score per topic,
    logs the attempt, and updates the mastery_scores table.
    Returns: { topic_id: mastery_score }
    """
    question_ids = [a.question_id for a in answers]
    questions = db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    question_map = {q.id: q for q in questions}

    topic_correct_weight = defaultdict(float)
    topic_total_weight = defaultdict(float)

    for ans in answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue  # silently skip invalid question ids

        weight = DIFFICULTY_WEIGHTS.get(question.difficulty, 1)
        topic_total_weight[question.topic_id] += weight

        if ans.selected_option == question.correct_answer:
            topic_correct_weight[question.topic_id] += weight

    mastery_result = {}

    for topic_id, total_weight in topic_total_weight.items():
        correct_weight = topic_correct_weight.get(topic_id, 0)
        score = round(correct_weight / total_weight, 3) if total_weight > 0 else 0.0
        mastery_result[topic_id] = score

        # Log the raw attempt
        db.add(QuizAttempt(
            user_id=user_id,
            topic_id=topic_id,
            quiz_type="diagnostic",
            score=score,
        ))

        # Update existing mastery row, or create a new one
        mastery_row = db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == topic_id
        ).first()

        level = classify_mastery_level(score)

        if mastery_row:
            mastery_row.mastery_score = score
            mastery_row.mastery_level = level
            mastery_row.last_updated = datetime.utcnow()
        else:
            db.add(MasteryScore(
                user_id=user_id,
                topic_id=topic_id,
                mastery_score=score,
                mastery_level=level,
            ))

    db.commit()
    return mastery_result