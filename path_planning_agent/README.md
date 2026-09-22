# Path Planning Agent

A pure, framework-independent, domain-driven learning path planning and prerequisite gating engine.

## Key Features

- **Pure Python Architecture**: No external runtime dependencies (zero database or framework lock-in).
- **Concept Graph DAG**: Fast topological sorting (Kahn's algorithm) and cycle detection.
- **Strict Prerequisite Gating**: Topics are blocked until all immediate prerequisites reach the configured mastery threshold (default: 75%).
- **Weekly Learning Budgeting**: Automatically fits scheduled topics to the student's weekly study budget and defers overflow topics.
- **Actionable Next-Topic Selection**: Instant identification of the next optimal topic to learn.
- **Pluggable Provider Boundary**: Simple adapter interfaces (`ConceptGraphProvider`, `MasteryProvider`, `StudentContextProvider`) allow connection to any persistence layer (PostgreSQL, SQLite, Supabase, memory).
- **Decoupled CMAB Integration**: Works alongside Contextual Multi-Armed Bandits (LinUCB) for resource format personalization.

## Installation

```bash
cd path_planning_agent
pip install -e .
```

## Quick Start

```python
from path_planning_agent import (
    PathPlanningAgent,
    ConceptGraph,
    TopicNode,
    InMemoryProvider,
    StudentProfile,
)

# 1. Build Graph
graph = ConceptGraph()
graph.add_topic(TopicNode(id="loops", name="Loops", difficulty="Beginner", estimated_duration=30))
graph.add_topic(TopicNode(id="recursion", name="Recursion", difficulty="Intermediate", estimated_duration=60))
graph.add_prerequisite("recursion", "loops")

# 2. Setup Provider with Student Data
provider = InMemoryProvider(graph=graph)
provider.set_student_profile(StudentProfile(user_id="user_1", weekly_time_budget=120))
provider.set_student_mastery("user_1", "loops", 0.85)

# 3. Plan Roadmap
agent = PathPlanningAgent(
    graph_provider=provider,
    mastery_provider=provider,
    context_provider=provider,
    mastery_threshold=0.75,
)

roadmap = agent.generate_roadmap("user_1")
print(f"Next topic: {roadmap.next_recommended_topic.topic.name}")
```

## Running the Standalone Demo

```bash
python examples/basic_example.py
```

## Running Tests

```bash
python -m unittest discover tests
```
