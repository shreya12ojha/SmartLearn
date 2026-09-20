from app.database import SessionLocal
from app.models import QuizAttempt, MasteryScore, QuizQuestion, TopicPrerequisite, Topic

db = SessionLocal()

# Delete in FK-safe order: dependents first, then parents
db.query(QuizAttempt).delete()
db.query(MasteryScore).delete()
db.query(QuizQuestion).delete()
db.query(TopicPrerequisite).delete()
db.query(Topic).delete()

db.commit()
db.close()
print("All quiz/topic/mastery data cleared. Ready for fresh seed.")