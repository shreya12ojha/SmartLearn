# Integration Guide

## Integrating with Custom Data Sources

The Path Planning Agent uses the **Provider Pattern** to decouple planning logic from persistence.

### 1. Implement Providers

```python
from path_planning_agent import (
    ConceptGraphProvider,
    MasteryProvider,
    StudentContextProvider,
    ConceptGraph,
    TopicNode,
    StudentMastery,
    StudentProfile,
)

class MyDatabaseGraphProvider(ConceptGraphProvider):
    def __init__(self, db_session):
        self.db = db_session

    def get_concept_graph(self) -> ConceptGraph:
        graph = ConceptGraph()
        # Query your DB for topics and prerequisites
        for topic in self.db.query(MyTopicModel).all():
            graph.add_topic(TopicNode(id=str(topic.id), name=topic.name, difficulty=topic.difficulty))
        for prereq in self.db.query(MyPrerequisiteModel).all():
            graph.add_prerequisite(str(prereq.topic_id), str(prereq.prerequisite_id))
        return graph

class MyDatabaseMasteryProvider(MasteryProvider):
    def __init__(self, db_session):
        self.db = db_session

    def get_mastery(self, user_id: str) -> dict[str, StudentMastery]:
        scores = {}
        for row in self.db.query(MyMasteryModel).filter_by(user_id=int(user_id)).all():
            scores[str(row.topic_id)] = StudentMastery(
                topic_id=str(row.topic_id),
                score=row.score,
                is_assessed=True,
            )
        return scores

class MyDatabaseContextProvider(StudentContextProvider):
    def __init__(self, db_session):
        self.db = db_session

    def get_student_context(self, user_id: str) -> StudentProfile:
        user = self.db.query(MyUserModel).get(int(user_id))
        return StudentProfile(
            user_id=str(user.id),
            weekly_time_budget=user.weekly_time_budget or 300,
            preferred_format=user.preferred_format or "video",
        )
```

### 2. Instantiate Planner

```python
agent = PathPlanningAgent(
    graph_provider=MyDatabaseGraphProvider(session),
    mastery_provider=MyDatabaseMasteryProvider(session),
    context_provider=MyDatabaseContextProvider(session),
    mastery_threshold=0.75,
)

roadmap = agent.generate_roadmap(user_id="42")
```
