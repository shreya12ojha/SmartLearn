from app.database import SessionLocal
from app.models import Topic, QuizQuestion

db = SessionLocal()

# Seed topics
topics_data = [
    {"name": "Loops", "domain": "DSA", "difficulty_level": "Beginner"},
    {"name": "Recursion", "domain": "DSA", "difficulty_level": "Intermediate"},
    {"name": "Arrays", "domain": "DSA", "difficulty_level": "Beginner"},
]

topic_objs = {}
for t in topics_data:
    topic = Topic(**t)
    db.add(topic)
    db.flush()  # so topic.id is available before commit
    topic_objs[t["name"]] = topic

# Seed a few sample questions
questions_data = [
    {
        "topic": "Loops",
        "question_text": "What will `for i in range(3): print(i)` output?",
        "options": {"A": "0 1 2", "B": "1 2 3", "C": "0 1 2 3", "D": "Error"},
        "correct_answer": "A",
        "difficulty": "easy",
    },
    {
        "topic": "Recursion",
        "question_text": "What is the base case in a recursive factorial function?",
        "options": {"A": "n == 0", "B": "n == 1", "C": "n < 0", "D": "Both A and B are valid depending on implementation"},
        "correct_answer": "D",
        "difficulty": "medium",
    },
]

for q in questions_data:
    question = QuizQuestion(
        topic_id=topic_objs[q["topic"]].id,
        question_text=q["question_text"],
        options=q["options"],
        correct_answer=q["correct_answer"],
        difficulty=q["difficulty"],
    )
    db.add(question)

db.commit()
db.close()
print("Seed data inserted successfully.")