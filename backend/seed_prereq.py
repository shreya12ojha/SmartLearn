from app.database import SessionLocal
from app.models import Topic, TopicPrerequisite

db = SessionLocal()

loops = db.query(Topic).filter(Topic.name == "Loops").first()
recursion = db.query(Topic).filter(Topic.name == "Recursion").first()
arrays = db.query(Topic).filter(Topic.name == "Arrays").first()

if not all([loops, recursion, arrays]):
    raise Exception("One or more topics not found — check your topics table first.")

prerequisites = [
    # Recursion requires Loops
    TopicPrerequisite(topic_id=recursion.id, prerequisite_topic_id=loops.id),
    # Recursion also requires Arrays (just as an example of multiple prerequisites)
    TopicPrerequisite(topic_id=recursion.id, prerequisite_topic_id=arrays.id),
]

db.add_all(prerequisites)
db.commit()
db.close()
print("Prerequisite relationships seeded.")