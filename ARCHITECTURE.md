# SmartLearn Architecture: Path Planning + Personalization + CMAB Module

## 1. Module Responsibilities & Core Principles

This module solves two independent problems with strict separation of concerns:

1. **Path Planning Agent**:
   - **Question Answered**: *"What should the student study next?"*
   - **Inputs**: Concept Graph (topics + prerequisite edges), Student Mastery Scores, Weekly Time Budget.
   - **Outputs**: Personalized Roadmap (`MASTERED`, `SCHEDULED`, `BLOCKED`, `DEFERRED`) and next actionable topic.
   - **Gating Rule**: Topics are strictly blocked if any immediate prerequisite is below the authoritative **75%** threshold.

2. **Contextual Multi-Armed Bandit (LinUCB)**:
   - **Question Answered**: *"How should the student study that topic?"*
   - **Inputs**: Student context vector $x \in \mathbb{R}^7$ (current mastery, normalized budget, preferred format one-hot, topic difficulty).
   - **Outputs**: Format selection (`video`, `text`, `practice`, `interactive`) with exploration-exploitation tradeoff ($\alpha = 0.5$) and matching learning resource.
   - **Feedback & Reward**: $r = \text{post\_mastery} - \text{pre\_mastery}$ calculated after quiz completion, triggering transaction-safe LinUCB updates.

---

## 2. Component Structure

```
SmartLearn/
├── backend/
│   ├── app/
│   │   ├── models.py                  # Topic, TopicPrerequisite, MasteryScore, LearningResource, BanditInteraction, BanditModelState
│   │   ├── schemas.py                 # RoadmapResponse, NextTopicResponse, ResourceRecommendationResponse, BanditFeedbackRequest/Response
│   │   ├── cmab.py                    # Production LinUCBBanditService with row-level transaction safety
│   │   ├── path_planning_agent.py     # SQLAlchemyConceptGraphProvider, SQLAlchemyMasteryProvider, SQLAlchemyStudentContextProvider
│   │   ├── path_planning_routes.py    # FastAPI routes for roadmap, next-topic, recommendations, feedback, and resources
│   │   └── main.py                    # Registered routers & CORS enabled for http://localhost:5173
│   ├── seed_resources.py              # Idempotent seeder for curated DSA learning resources across 4 formats
│   └── test_path_planning_backend.py  # Backend integration test suite
├── learning-app-frontend/
│   ├── src/
│   │   ├── api/realApi.js             # API client methods for path planning & recommendations
│   │   ├── pages/Roadmap.jsx          # Live Personalized Roadmap with Next Topic hero & pacing
│   │   ├── pages/RealDsaQuiz.jsx      # Quiz completion triggering LinUCB feedback loop
│   │   └── App.css                    # Modern styling for badges, hero card, and pacing bars
├── path_planning_agent/               # Reusable standalone package (zero DB dependencies)
│   ├── path_planning_agent/
│   │   ├── concept_graph.py           # Pure-Python DAG, Kahn's topo sort, cycle detection
│   │   ├── planner.py                 # Core PathPlanningAgent logic
│   │   ├── models.py                  # Domain entities (TopicNode, RoadmapResult, etc.)
│   │   └── providers.py               # Abstract provider interfaces & InMemoryProvider
│   ├── examples/basic_example.py      # Standalone demo running without DATABASE_URL
│   └── tests/                         # Standalone test suite (100% pass)
├── simulation/
│   ├── simulate_cmab.py               # Synthetic student simulation (LinUCB vs Random over 1000 rounds)
│   └── results/                       # Generated charts and numerical evaluation report
└── FLOWCHARTS.md                      # Comprehensive Mermaid diagrams
```

---

## 3. Authoritative Rules & Infrastructure

- **Mastery Threshold**: Defined authoritatively in `backend/app/assessment_agent.py` as **0.75**. The Path Planning Agent strictly preserves this threshold.
- **Budget Respect**: Topic durations default to Beginner = 30m, Intermediate = 60m, Advanced = 90m (or topic-specific durations). Total scheduled minutes never exceed the student's `weekly_time_budget`.
- **Database Concurrency**: LinUCB parameter updates use `SELECT ... FOR UPDATE` row-level locking on `bandit_model_state` to prevent race conditions or lost updates across multiple workers.
- **Zero Duplicate Systems**: Directly consumes existing `User`, `Topic`, `TopicPrerequisite`, `MasteryScore`, and `QuizQuestion` tables without duplication.
