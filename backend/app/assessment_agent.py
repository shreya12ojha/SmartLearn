from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime

from app.models import QuizQuestion, QuizAttempt, MasteryScore, User

DIFFICULTY_WEIGHTS = {"easy": 1, "medium": 2, "hard": 3}


def classify_mastery_level(score: float) -> str:
    if score < 0.4:
        return "Beginner"
    elif score < 0.75:
        return "Intermediate"
    else:
        return "Advanced"


class InvalidUserError(Exception):
    pass


class InvalidSubmissionError(Exception):
    pass


def score_quiz(db: Session, user_id: int, answers: list, quiz_type: str = "diagnostic"):
    # --- Edge case: user must exist ---
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise InvalidUserError(f"User with id {user_id} does not exist")

    # --- Edge case: deduplicate answers by question_id (keep the last one submitted) ---
    deduped_answers = {}
    for ans in answers:
        deduped_answers[ans.question_id] = ans
    answers = list(deduped_answers.values())

    question_ids = [a.question_id for a in answers]
    questions = db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    question_map = {q.id: q for q in questions}

    topic_correct_weight = defaultdict(float)
    topic_total_weight = defaultdict(float)
    valid_answers_found = False
    results = []

    for ans in answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue  # skip invalid/unknown question_id

        valid_answers_found = True
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

    # --- Edge case: every submitted question_id was invalid ---
    if not valid_answers_found:
        raise InvalidSubmissionError("None of the submitted question_ids are valid")

    mastery_result = {}

    for topic_id, total_weight in topic_total_weight.items():
        correct_weight = topic_correct_weight.get(topic_id, 0)
        score = round(correct_weight / total_weight, 3) if total_weight > 0 else 0.0
        mastery_result[topic_id] = score

        db.add(QuizAttempt(
            user_id=user_id,
            topic_id=topic_id,
            quiz_type=quiz_type,
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