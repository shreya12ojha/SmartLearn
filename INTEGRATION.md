# SmartLearn: Full-Stack Integration Guide

This guide describes how the **Path Planning Agent**, **CMAB / LinUCB Service**, **FastAPI Backend**, and **React / Vite Frontend** integrate to form an end-to-end adaptive learning system.

---

## 1. Integration Architecture Overview

```
Frontend (React 19 + Vite)
    │
    │ HTTP / JSON (realApi.js)
    ▼
FastAPI Routing Layer
    │
    ├─► /api/path-planning/roadmap/{user_id}   ──► PathPlanningAgent
    ├─► /api/path-planning/next-topic/{user_id} ──► PathPlanningAgent
    ├─► /api/recommendations/resource          ──► LinUCBBanditService
    ├─► /api/recommendations/feedback          ──► LinUCBBanditService (Row-Level Locking)
    └─► /api/quiz/submit                       ──► Assessment Agent (Authoritative Scoring)
    │
    ▼
SQLAlchemy Layer (PostgreSQL / Supabase)
    ├── User, Topic, TopicPrerequisite, MasteryScore
    ├── LearningResource (4 Formats: video, text, practice, interactive)
    └── BanditModelState, BanditInteraction
```

---

## 2. Backend Integration

### 2.1 Provider Adapters (`backend/app/path_planning_agent.py`)
The standalone `path_planning_agent` package interacts with SmartLearn's database through the **Provider Pattern**:

1. **`SQLAlchemyConceptGraphProvider`**:
   - Queries `Topic` and `TopicPrerequisite` tables.
   - Instantiates `TopicNode` and populates the `ConceptGraph` DAG.
2. **`SQLAlchemyMasteryProvider`**:
   - Queries `MasteryScore` for the student.
   - Normalizes scores to `StudentMastery` domain models.
3. **`SQLAlchemyStudentContextProvider`**:
   - Queries `User` table for `weekly_time_budget` and `preferred_format`.
   - Returns a `StudentProfile`.

### 2.2 LinUCB Service Integration (`backend/app/cmab.py`)
- **Context Construction**: `build_context_vector(...)` transforms student and topic attributes into a normalized 7-dimensional vector.
- **Arm Scoring**: Uses Gauss-Jordan elimination for exact $7\times 7$ matrix inversion with zero external native dependencies.
- **Concurrency-Safe Persistence**:
  ```python
  row = db.query(BanditModelState).filter(BanditModelState.arm_name == selected_arm).with_for_update().first()
  ```
  Applies `SELECT ... FOR UPDATE` row locking during feedback updates to guarantee atomic parameter updates under concurrent quiz completions.

---

## 3. Frontend Integration

### 3.1 Live API Client (`learning-app-frontend/src/api/realApi.js`)
Exposes asynchronous API methods:
- `fetchRoadmapReal(userId)`
- `fetchNextTopicReal(userId)`
- `fetchResourceRecommendation(userId, topicId)`
- `submitQuizReal(userId, answers)`
- `submitBanditFeedback({ userId, topicId, selectedArm, preMastery, postMastery })`
- `fetchResources(topicId, format)`

### 3.2 Roadmap UI (`learning-app-frontend/src/pages/Roadmap.jsx`)
- Displays the **Next Recommended Topic Hero Card** with the LinUCB-selected format badge (`VIDEO`, `TEXT`, `PRACTICE`, `INTERACTIVE`).
- Displays the **Curriculum Learning Order** with status badges:
  - `MASTERED` (Green checkmark, score $\ge 75\%$)
  - `SCHEDULED` (Rocket badge, unlocked and fits weekly budget)
  - `BLOCKED` (Lock badge, unfulfilled prerequisites listed)
  - `DEFERRED` (Hourglass badge, unlocked but exceeds budget)
- Provides **Weekly Time Budget Pacing Track** showing allocated vs. total minutes.
- Passes the recommended arm to the Quiz view when the student clicks *"Take Topic Quiz"*.

### 3.3 Quiz & Feedback Loop (`learning-app-frontend/src/pages/RealDsaQuiz.jsx`)
- Captures `preMastery` before the quiz attempt.
- Submits answers to `POST /api/quiz/submit`.
- Receives authoritative `postMastery` from the backend assessment system.
- Dispatches `POST /api/recommendations/feedback` with `selectedArm`, `preMastery`, and `postMastery`.
- Updates LinUCB bandit parameters in database and navigates back to the roadmap with newly unlocked topics.

---

## 4. Idempotent Data Seeding

### Seeding Curated Learning Resources (`backend/seed_resources.py`)
Covers all 11 DSA topics across all 4 learning formats (44+ resources).
Idempotency check:
```python
existing = db.query(LearningResource).filter(
    LearningResource.topic_id == topic.id,
    LearningResource.title == res["title"],
    LearningResource.format == res["format"],
).first()
if not existing:
    db.add(...)
```
Running `seed_resources.py` multiple times is safe and never creates duplicates.
