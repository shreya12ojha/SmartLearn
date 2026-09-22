from app.database import SessionLocal
from app.models import Topic, QuizQuestion

db = SessionLocal()

loops_topic = db.query(Topic).filter(Topic.name == "Loops").first()
recursion_topic = db.query(Topic).filter(Topic.name == "Recursion").first()

if not loops_topic or not recursion_topic:
    print("Required topics ('Loops', 'Recursion') not found. Run seed.py first.")
    db.close()
else:
    extra_questions = [
        {
            "topic_id": loops_topic.id,
            "question_text": "Which loop guarantees at least one execution?",
            "options": {"A": "for", "B": "while", "C": "do-while", "D": "None"},
            "correct_answer": "C",
            "difficulty": "medium",
        },
        {
            "topic_id": loops_topic.id,
            "question_text": "What does 'break' do inside a loop?",
            "options": {"A": "Skips current iteration", "B": "Exits the loop", "C": "Restarts the loop", "D": "Pauses execution"},
            "correct_answer": "B",
            "difficulty": "easy",
        },
        {
            "topic_id": recursion_topic.id,
            "question_text": "What happens if a recursive function has no base case?",
            "options": {"A": "It runs once", "B": "Stack overflow / infinite recursion", "C": "Compiler error", "D": "Nothing"},
            "correct_answer": "B",
            "difficulty": "hard",
        },
    ]

    added = 0
    skipped = 0
    for q in extra_questions:
        existing = (
            db.query(QuizQuestion)
            .filter(
                QuizQuestion.topic_id == q["topic_id"],
                QuizQuestion.question_text == q["question_text"],
            )
            .first()
        )
        if existing:
            skipped += 1
            continue
        db.add(QuizQuestion(**q))
        added += 1

    db.commit()
    db.close()
    print(f"Extra questions: {added} added, {skipped} already existed.")