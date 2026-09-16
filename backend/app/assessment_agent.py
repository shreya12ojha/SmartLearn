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


def score_quiz(db: Session, user_id: int, answers: list):
    """
    Takes raw answers, computes a weighted mastery score per topic,
    logs the attempt, updates mastery_scores, and returns both the
    topic-level mastery AND a per-question correct/incorrect breakdown.
    Returns: ({ topic_id: mastery_score }, [ {question_id, question_text,
              selected_option, correct_option, is_correct}, ... ])
    """
    question_ids = [a.question_id for a in answers]
    questions = db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    question_map = {q.id: q for q in questions}

    topic_correct_weight = defaultdict(float)
    topic_total_weight = defaultdict(float)
    results = []

    for ans in answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue  # silently skip invalid question ids

        weight = DIFFICULTY_WEIGHTS.get(question.difficulty, 1)
        topic_total_weight[question.topic_id] += weight

        is_correct = ans.selected_option == question.correct_answer
        if is_correct:
            topic_correct_weight[question.topic_id] += weight

        results.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "selected_option": ans.selected_option,
            "correct_option": question.correct_answer,
            "is_correct": is_correct,
        })

    mastery_result = {}

    for topic_id, total_weight in topic_total_weight.items():
        correct_weight = topic_correct_weight.get(topic_id, 0)
        score = round(correct_weight / total_weight, 3) if total_weight > 0 else 0.0
        mastery_result[topic_id] = score

        db.add(QuizAttempt(
            user_id=user_id,
            topic_id=topic_id,
            quiz_type="diagnostic",
            score=score,
        ))

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
    return mastery_result, results