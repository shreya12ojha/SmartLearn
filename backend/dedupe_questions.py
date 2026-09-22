"""
One-off cleanup script: removes duplicate QuizQuestion rows caused by
seed.py / seed_more.py having been run more than once before they had
idempotency checks. Keeps the earliest (lowest id) row for each
(topic_id, question_text) pair and deletes the rest.

Safe to run multiple times - it's a no-op once the data is clean.
"""

from app.database import SessionLocal
from app.models import QuizQuestion


def dedupe_questions():
    db = SessionLocal()
    try:
        questions = db.query(QuizQuestion).order_by(QuizQuestion.id.asc()).all()

        seen = {}
        duplicates = []

        for q in questions:
            key = (q.topic_id, q.question_text)
            if key in seen:
                duplicates.append(q)
            else:
                seen[key] = q

        if not duplicates:
            print("No duplicate questions found. Nothing to clean up.")
            return

        print(f"Found {len(duplicates)} duplicate question rows. Deleting...")
        for dup in duplicates:
            db.delete(dup)

        db.commit()
        print(f"Deleted {len(duplicates)} duplicate questions. Database is now clean.")
    except Exception as e:
        db.rollback()
        print(f"Error while deduping questions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dedupe_questions()