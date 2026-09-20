import json
from pathlib import Path

from app.database import SessionLocal
from app.models import Topic, TopicPrerequisite, QuizQuestion

db = SessionLocal()

data_path = Path(__file__).parent / "data" / "question_bank.json"
with open(data_path, "r") as f:
    data = json.load(f)

# ---------- 1. Seed Topics ----------
topic_map = {}  # name -> Topic object

for t in data["topics"]:
    existing = db.query(Topic).filter(Topic.name == t["name"]).first()
    if existing:
        topic_map[t["name"]] = existing
    else:
        new_topic = Topic(
            name=t["name"],
            domain=t["domain"],
            difficulty_level=t["difficulty_level"],
        )
        db.add(new_topic)
        db.flush()  # get new_topic.id before commit
        topic_map[t["name"]] = new_topic

db.commit()
print(f"Topics ready: {len(topic_map)}")

# ---------- 2. Seed Prerequisites ----------
prereq_count = 0
for p in data["prerequisites"]:
    topic_obj = topic_map[p["topic"]]
    prereq_obj = topic_map[p["prerequisite"]]

    existing = (
        db.query(TopicPrerequisite)
        .filter(
            TopicPrerequisite.topic_id == topic_obj.id,
            TopicPrerequisite.prerequisite_topic_id == prereq_obj.id,
        )
        .first()
    )
    if not existing:
        db.add(TopicPrerequisite(
            topic_id=topic_obj.id,
            prerequisite_topic_id=prereq_obj.id,
        ))
        prereq_count += 1

db.commit()
print(f"New prerequisite edges added: {prereq_count}")

# ---------- 3. Seed Questions ----------
question_count = 0
for q in data["questions"]:
    topic_obj = topic_map[q["topic"]]

    existing = (
        db.query(QuizQuestion)
        .filter(
            QuizQuestion.topic_id == topic_obj.id,
            QuizQuestion.question_text == q["question_text"],
        )
        .first()
    )
    if not existing:
        db.add(QuizQuestion(
            topic_id=topic_obj.id,
            question_text=q["question_text"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            difficulty=q["difficulty"],
        ))
        question_count += 1

db.commit()
db.close()
print(f"New questions added: {question_count}")
print("Full question bank seeding complete.")