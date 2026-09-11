from app.database import SessionLocal
from app.models import Topic, QuizQuestion

db = SessionLocal()

loops_topic = db.query(Topic).filter(Topic.name == "Loops").first()
recursion_topic = db.query(Topic).filter(Topic.name == "Recursion").first()

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

for q in extra_questions:
    db.add(QuizQuestion(**q))

db.commit()
db.close()
print("Extra questions added.")