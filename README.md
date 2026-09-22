# SmartLearn: Adaptive Learning Platform

SmartLearn is an intelligent, personalized learning platform that integrates **DAG-based Path Planning** with a **Contextual Multi-Armed Bandit (LinUCB)** recommendation engine to deliver a truly adaptive curriculum for students.

---

## 1. System Architecture & Core Modules

SmartLearn cleanly separates the two fundamental questions of adaptive education:

| Module | Core Question | Primary Inputs | Core Algorithm / Model | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Path Planning Agent** | *"WHAT should the student learn next?"* | Concept Graph, Student Mastery, Weekly Time Budget | Kahn's Algorithm, Cycle Detection, 75% Threshold Gating | Personalized Roadmap (`MASTERED`, `SCHEDULED`, `BLOCKED`, `DEFERRED`) |
| **CMAB (LinUCB)** | *"HOW should the student learn it?"* | Student Context Vector $x \in \mathbb{R}^7$ | Linear Upper Confidence Bound ($\alpha = 0.5$) | Recommended Learning Format (`video`, `text`, `practice`, `interactive`) & Resource |

### Closed-Loop Architecture

```
Student Logs In
       ↓
Fetch Student Profile (Time Budget, Preferred Format)
       ↓
Retrieve Current Mastery & Concept Graph Prerequisites
       ↓
Path Planning Agent Generates Roadmap (75% Mastery Gating)
       ↓
Select Next Actionable Topic (e.g., Linked Lists)
       ↓
CMAB (LinUCB) Evaluates Context Vector (d = 7)
       ↓
Recommends Optimal Format & Learning Resource
       ↓
Student Studies & Completes Topic Quiz
       ↓
Authoritative Backend Assessment Engine Scores Quiz & Updates Mastery
       ↓
Reward Calculated: r = post_mastery - pre_mastery
       ↓
Transaction-Safe LinUCB Update (Row-Level Locking on bandit_model_state)
       ↓
Subsequent Recommendations & Downstream Topics Unlocked
```

---

## 2. Path Planning & Concept Graph

### Concept Graph (DAG)
- Represented as a Directed Acyclic Graph where edges point from **Prerequisite $\to$ Dependent**.
- Supports:
  - **Topological Sorting** using Kahn's algorithm.
  - **Cycle Detection** with DFS back-edge detection (raises `CycleDetectedError`).
  - **Transitive Prerequisite Resolution** via BFS traversal.
  - **Prerequisite Mastery Verification**: A topic is unlocked if and only if **all** immediate prerequisites meet or exceed the authoritative **0.75 (75%)** threshold.

### Weekly Time Budget Allocation
- Topics have realistic duration estimates:
  - Beginner: 30 minutes
  - Intermediate: 60 minutes
  - Advanced: 90 minutes
- The agent schedules unlocked, unmastered topics until the student's `weekly_time_budget` is filled.
- Any remaining unlocked topics that exceed the budget are labeled `DEFERRED`.

---

## 3. Contextual Multi-Armed Bandit (LinUCB)

### Supported Arms
- `video`: Video tutorials and animated walkthroughs.
- `text`: Written articles and deep-dive documentation.
- `practice`: Coding problems and hands-on exercises.
- `interactive`: Memory visualizers and interactive algorithm steppers.

### 7-Dimensional Context Vector ($x \in \mathbb{R}^7$)
1. $x[0]$: `current_mastery` ($[0.0, 1.0]$)
2. $x[1]$: `normalized_budget` ($\text{weekly\_budget} / 600.0$ clamped to $[0.0, 1.0]$)
3. $x[2]$: `is_pref_video` ($1.0$ or $0.0$)
4. $x[3]$: `is_pref_text` ($1.0$ or $0.0$)
5. $x[4]$: `is_pref_practice` ($1.0$ or $0.0$)
6. $x[5]$: `is_pref_interactive` ($1.0$ or $0.0$)
7. $x[6]$: `topic_difficulty` ($\text{Beginner}=0.33, \text{Intermediate}=0.66, \text{Advanced}=1.0$)

### LinUCB Mathematical Formulation
For each arm $a$:
$$\theta_a = A_a^{-1} b_a$$
$$p_a = \theta_a^T x + \alpha \sqrt{x^T A_a^{-1} x}$$
$$\text{Selected Arm } a^* = \arg\max_{a} p_a$$

Upon receiving learning feedback with reward $r = \text{post\_mastery} - \text{pre\_mastery}$:
$$A_{a^*} \leftarrow A_{a^*} + x x^T$$
$$b_{a^*} \leftarrow b_{a^*} + r x$$

### Concurrency Safety & Persistence
- State is persisted in `bandit_model_state` table with matrix $A_a$ and vector $b_a$.
- Model updates use `with_for_update()` row-level locking to prevent lost updates across concurrent workers.

---

## 4. Repository Structure

```
SmartLearn/
├── backend/
│   ├── app/
│   │   ├── auth.py                    # JWT auth & password hashing
│   │   ├── auth_routes.py             # Signup and Login endpoints
│   │   ├── cmab.py                    # Production LinUCB Service with DB locking
│   │   ├── database.py                # Database connection & session factory
│   │   ├── models.py                  # SQLAlchemy models (User, Topic, MasteryScore, LearningResource, BanditModelState, etc.)
│   │   ├── path_planning_agent.py     # SQLAlchemy providers bridging DB to domain
│   │   ├── path_planning_routes.py    # Roadmap, next-topic, recommendations & feedback endpoints
│   │   ├── quiz.py                    # Quiz questions & submission endpoint
│   │   ├── assessment_agent.py        # Authoritative scoring engine
│   │   └── schemas.py                 # Pydantic schemas
│   ├── .env.example                   # Environment configuration template
│   ├── seed_resources.py              # Idempotent learning resource seeder (11 DSA topics, 4 formats)
│   ├── seed_full_qb.py                # Full question bank & prerequisite seeder
│   ├── test_path_planning_backend.py  # Backend integration test suite
│   └── test_e2e_integration.py        # Complete end-to-end student lifecycle test suite
├── learning-app-frontend/             # React 19 + Vite frontend
│   ├── src/
│   │   ├── api/realApi.js             # API client for backend
│   │   ├── pages/Roadmap.jsx          # Live Personalized Roadmap UI with Next Topic Hero card
│   │   ├── pages/RealDsaQuiz.jsx      # Quiz interface triggering LinUCB feedback loop
│   │   └── App.css                    # Modern UI styles, badges, and progress tracks
│   └── package.json
├── path_planning_agent/               # Reusable standalone package (zero DB dependencies)
│   ├── path_planning_agent/
│   │   ├── concept_graph.py           # DAG, Kahn's algorithm, cycle detection
│   │   ├── planner.py                 # PathPlanningAgent implementation
│   │   ├── models.py                  # TopicNode, StudentMastery, RoadmapResult
│   │   └── providers.py               # Abstract provider interfaces & InMemoryProvider
│   ├── examples/basic_example.py      # Standalone CLI demonstration
│   └── tests/                         # Standalone unit tests
├── simulation/
│   ├── simulate_cmab.py               # 1000-round synthetic student simulation (LinUCB vs Random)
│   └── results/                       # Generated charts and evaluation report
├── ARCHITECTURE.md                    # Technical architecture specification
├── INTEGRATION.md                     # Frontend & backend integration guide
├── API_REFERENCE.md                   # Complete REST API reference
├── EXAMPLE.md                         # Detailed worked example
└── FLOWCHARTS.md                      # Mermaid process and architecture diagrams
```

---

## 5. Quick Start & Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL (Supabase or local instance for production)

### Environment Configuration
Copy the template to `.env`:
```powershell
cp backend/.env.example backend/.env
```
Configure your database connection and secrets:
```ini
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
SECRET_KEY=your-secure-random-secret-key-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 1. Standalone Demo (Zero DB Required)
```powershell
.\.venv_win\Scripts\python.exe path_planning_agent/examples/basic_example.py
```

### 2. Backend Server
```powershell
# In backend directory
cd backend
..\.venv_win\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
API Documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Application
```powershell
cd learning-app-frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 4. Synthetic CMAB Simulation
```powershell
.\.venv_win\Scripts\python.exe simulation/simulate_cmab.py
```
Output charts and reports are saved to `simulation/results/`.

---

## 6. Testing

### Run All Tests
```powershell
# 1. Standalone package tests
.\.venv_win\Scripts\python.exe -m unittest discover -s path_planning_agent/tests

# 2. Backend integration tests
$env:PYTHONPATH="backend;path_planning_agent"; .\.venv_win\Scripts\python.exe backend/test_path_planning_backend.py

# 3. Real End-to-End lifecycle test
$env:PYTHONPATH="backend;path_planning_agent"; .\.venv_win\Scripts\python.exe backend/test_e2e_integration.py

# 4. Frontend production build
cd learning-app-frontend; npm run build
```