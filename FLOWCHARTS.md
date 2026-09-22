# SmartLearn: Architectural & Process Flowcharts

This document provides formal Mermaid diagrams documenting the architectural, mathematical, and data flows of the **Path Planning Agent**, **CMAB/LinUCB Recommendation Engine**, and **SmartLearn Learning Platform**.

---

## 1. Overall SmartLearn Architecture

```mermaid
flowchart TD
    subgraph ClientLayer ["Frontend Layer (React 19 + Vite)"]
        UI_Dash["Student Dashboard"]
        UI_Roadmap["Personalized Roadmap Page"]
        UI_Hero["Next Topic Hero Card (LinUCB Recommended Format)"]
        UI_Quiz["DSA Topic Quiz / Assessment"]
    end

    subgraph BackendAPI ["FastAPI Routing Layer"]
        API_Roadmap["GET /api/path-planning/roadmap/{user_id}"]
        API_Next["GET /api/path-planning/next-topic/{user_id}"]
        API_Rec["GET /api/recommendations/resource"]
        API_Feedback["POST /api/recommendations/feedback"]
        API_Quiz["POST /api/quiz/submit"]
    end

    subgraph CoreEngine ["Path Planning & Personalization Engines"]
        PPA["Path Planning Agent (Kahn's Topo Sort + 75% Threshold Gating)"]
        LinUCB["LinUCB Bandit Service (7-dim Context Vector, alpha=0.5)"]
        AssessmentAgent["Authoritative Assessment Engine"]
    end

    subgraph DataLayer ["PostgreSQL / Database Models"]
        DB_Topics["Topic & TopicPrerequisite Tables"]
        DB_Mastery["MasteryScore Table"]
        DB_User["User Table (weekly_time_budget, preferred_format)"]
        DB_Resources["LearningResource Table (4 Formats)"]
        DB_BanditState["BanditModelState (A Matrix 7x7, b Vector 7x1)"]
        DB_Interactions["BanditInteraction Table"]
    end

    %% Connections
    UI_Dash --> UI_Roadmap
    UI_Roadmap --> API_Roadmap
    API_Roadmap --> PPA

    DB_Topics --> PPA
    DB_Mastery --> PPA
    DB_User --> PPA

    PPA --> API_Roadmap
    API_Roadmap --> UI_Hero

    UI_Hero --> API_Rec
    API_Rec --> LinUCB
    DB_Resources --> LinUCB
    DB_BanditState --> LinUCB
    LinUCB --> API_Rec
    API_Rec --> UI_Hero

    UI_Hero --> UI_Quiz
    UI_Quiz --> API_Quiz
    API_Quiz --> AssessmentAgent
    AssessmentAgent --> DB_Mastery

    UI_Quiz --> API_Feedback
    API_Feedback --> LinUCB
    LinUCB --> DB_BanditState
    LinUCB --> DB_Interactions
```

---

## 2. Path Planning Algorithm

Answers: **"What should the student learn next?"**

```mermaid
flowchart TD
    Start([Start Path Planning]) --> Ingest[Fetch Topics, Prerequisites, Mastery, and Weekly Time Budget]
    Ingest --> BuildDAG[Construct ConceptGraph DAG]
    BuildDAG --> CheckCycles{Cycle Detected?}
    CheckCycles -- Yes --> Error[Raise CycleDetectedError]
    CheckCycles -- No --> TopoSort[Execute Kahn's Algorithm for Topological Ordering]

    TopoSort --> LoopTopics[For each Topic in Topological Order]

    LoopTopics --> CheckMastery{Mastery >= 75%?}
    CheckMastery -- Yes --> MarkMastered["Mark Status: MASTERED<br/>(Skip from active study schedule)"]

    CheckMastery -- No --> CheckPrereqs{All Direct Prerequisites >= 75%?}
    CheckPrereqs -- No --> MarkBlocked["Mark Status: BLOCKED<br/>(List specific blocking prerequisites)"]

    CheckPrereqs -- Yes --> CheckBudget{Allocated Time + Topic Duration <= Weekly Budget?}
    CheckBudget -- Yes --> MarkScheduled["Mark Status: SCHEDULED<br/>(Add Duration to Allocated Minutes)"]
    CheckBudget -- No --> MarkDeferred["Mark Status: DEFERRED<br/>(Prerequisites met but exceeds weekly minutes)"]

    MarkScheduled --> NextCheck{Is Next Recommended Topic already assigned?}
    NextCheck -- No --> SetNext[Set as Next Recommended Topic]
    NextCheck -- Yes --> ContinueLoop[Continue Evaluation]

    MarkMastered --> ContinueLoop
    MarkBlocked --> ContinueLoop
    MarkDeferred --> ContinueLoop
    SetNext --> ContinueLoop

    ContinueLoop --> MoreTopics{More Topics Remaining?}
    MoreTopics -- Yes --> LoopTopics
    MoreTopics -- No --> FinalizeRoadmap[Assemble RoadmapResult with Remaining Budget & Summary]
    FinalizeRoadmap --> End([Return Personalized Roadmap])
```

---

## 3. CMAB/LinUCB Recommendation Loop

Answers: **"How should the student learn it?"**

```mermaid
flowchart TD
    subgraph ContextExtraction ["1. Context Vector Assembly (d = 7)"]
        C1["x[0]: Current Mastery (0.0 to 1.0)"]
        C2["x[1]: Normalized Weekly Budget (budget / 600)"]
        C3["x[2]: Is Preferred Format Video (1.0 or 0.0)"]
        C4["x[3]: Is Preferred Format Text (1.0 or 0.0)"]
        C5["x[4]: Is Preferred Format Practice (1.0 or 0.0)"]
        C6["x[5]: Is Preferred Format Interactive (1.0 or 0.0)"]
        C7["x[6]: Topic Difficulty (Beginner=0.33, Intermediate=0.66, Advanced=1.0)"]
    end

    subgraph LinUCBInference ["2. LinUCB Arm Scoring & Selection"]
        LoadA["Load A_a Matrix (7x7) and b_a Vector (7x1) from DB"]
        ComputeTheta["Compute ridge regression: theta_a = A_a^(-1) * b_a"]
        ComputeUCB["Compute score: p_a = theta_a^T * x + alpha * sqrt(x^T * A_a^(-1) * x)"]
        SelectArm["Select Arm a* = argmax(p_a) from {video, text, practice, interactive}"]
    end

    subgraph ResourceRetrieval ["3. Learning Resource Matching"]
        GetRes["Query LearningResource for (topic_id, selected_arm)"]
        ReturnRec["Return selected arm, UCB score, exploration bonus & resource"]
    end

    ContextExtraction --> LoadA
    LoadA --> ComputeTheta
    ComputeTheta --> ComputeUCB
    ComputeUCB --> SelectArm
    SelectArm --> GetRes
    GetRes --> ReturnRec
```

---

## 4. Quiz → Mastery → Reward → Feedback Loop

```mermaid
flowchart TD
    subgraph QuizExecution ["1. Assessment Execution"]
        StartQuiz["Student Opens Topic Quiz"]
        PreMastery["Capture Pre-Mastery (from current MasteryScore)"]
        SubmitAnswers["Student Submits Answers to POST /api/quiz/submit"]
        ScoreEngine["Backend Assessment Engine Scores Submission"]
        SaveAttempt["Save QuizAttempt record in DB"]
        UpdateMastery["Update MasteryScore in DB (Authoritative Mastery)"]
        GetPostMastery["Obtain Post-Mastery Score"]
    end

    subgraph RewardCalculation ["2. Authoritative Reward Calculation"]
        ComputeReward["Reward r = post_mastery - pre_mastery<br/>Clamped to [-1.0, 1.0]"]
    end

    subgraph LinUCBUpdate ["3. Transaction-Safe LinUCB Update"]
        PostFeedback["Send POST /api/recommendations/feedback"]
        RebuildContext["Reconstruct context vector x for (user, topic, pre_mastery)"]
        RowLock["Acquire Row Lock on bandit_model_state (SELECT ... FOR UPDATE)"]
        UpdateA["Update Matrix: A_a = A_a + x * x^T"]
        UpdateB["Update Vector: b_a = b_a + r * x"]
        CommitDB["Commit Updated State to DB & Record BanditInteraction"]
        ReadyNext["Model Parameters Updated: Ready for Next Adaptive Recommendation"]
    end

    StartQuiz --> PreMastery
    PreMastery --> SubmitAnswers
    SubmitAnswers --> ScoreEngine
    ScoreEngine --> SaveAttempt
    SaveAttempt --> UpdateMastery
    UpdateMastery --> GetPostMastery
    GetPostMastery --> ComputeReward
    ComputeReward --> PostFeedback
    PostFeedback --> RebuildContext
    RebuildContext --> RowLock
    RowLock --> UpdateA
    UpdateA --> UpdateB
    UpdateB --> CommitDB
    CommitDB --> ReadyNext
```

---

## 5. End-to-End SmartLearn Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Frontend as React Frontend (Vite)
    participant API as FastAPI Backend
    participant Planner as PathPlanningAgent
    participant CMAB as LinUCB Engine
    participant DB as PostgreSQL / Database

    Student->>Frontend: Logs in & views Roadmap
    Frontend->>API: GET /api/path-planning/roadmap/{user_id}
    API->>DB: Query Topics, Prerequisites, Mastery, User Profile
    DB-->>API: Graph Nodes, Edges & Student State
    API->>Planner: generate_roadmap(user_id)
    Planner-->>API: RoadmapResult (Next Topic: Linked Lists, Status: Scheduled)
    API-->>Frontend: Roadmap JSON
    Frontend-->>Student: Displays Roadmap (Scheduled, Mastered, Blocked)

    Frontend->>API: GET /api/recommendations/resource?user_id=1&topic_id=2
    API->>CMAB: recommend_resource_format(user, topic, current_mastery)
    CMAB->>DB: Query A_a, b_a from bandit_model_state & LearningResource
    DB-->>CMAB: Arm state & Resource row
    CMAB-->>API: Recommendation (Arm: PRACTICE, Resource: "Interactive Linked Lists")
    API-->>Frontend: Recommendation JSON
    Frontend-->>Student: Displays Hero Card: "Study Practice Now" + "Take Topic Quiz"

    Student->>Frontend: Studies Resource & Clicks "Take Topic Quiz"
    Frontend->>API: POST /api/quiz/submit (user_id, answers)
    API->>DB: Score Quiz, Save QuizAttempt, Update MasteryScore
    DB-->>API: Updated Post-Mastery Score (e.g., 85%)
    API-->>Frontend: Quiz Results & New Mastery
    Frontend-->>Student: Displays Question Review & Score (85%)

    Frontend->>API: POST /api/recommendations/feedback (user_id, topic_id, arm, pre: 35%, post: 85%)
    API->>CMAB: update_model(reward = +0.50)
    CMAB->>DB: Transaction-safe update of A_practice and b_practice (row lock)
    DB-->>CMAB: Confirmed
    CMAB-->>API: Update Success (reward: +0.50)
    API-->>Frontend: 200 OK
    Frontend-->>Student: Returns to Roadmap: Linked Lists now MASTERED, Trees UNLOCKED!
```

---

## 6. Standalone Path Planning Agent Architecture

```mermaid
graph TD
    subgraph PackageRoot ["path_planning_agent/ (Pure Python, Zero DB/FastAPI Dependencies)"]
        CoreInit["__init__.py<br/>(Exports Agent, Graph, Models, Providers)"]
        Planner["planner.py<br/>(PathPlanningAgent - 75% Threshold, Weekly Budget)"]
        Graph["concept_graph.py<br/>(ConceptGraph, Kahn's Topo Sort, Cycle Detection)"]
        Models["models.py<br/>(TopicNode, StudentMastery, RoadmapResult, RoadmapItem)"]
        Providers["providers.py<br/>(ConceptGraphProvider, MasteryProvider, InMemoryProvider)"]
    end

    subgraph Consumer1 ["SmartLearn Production Backend"]
        SL_Adapters["backend/app/path_planning_agent.py<br/>(SQLAlchemy ConceptGraph, Mastery & Context Providers)"]
        SL_Routes["backend/app/path_planning_routes.py<br/>(FastAPI REST Endpoints)"]
    end

    subgraph Consumer2 ["Third-Party LMS / External Integrations"]
        Custom_Provider["CustomGraphProvider<br/>CustomMasteryProvider"]
    end

    subgraph DemoAndTests ["Standalone Verification"]
        Demo["examples/basic_example.py<br/>(Independent CLI Demo)"]
        Tests["tests/<br/>test_concept_graph.py<br/>test_planner.py"]
    end

    CoreInit --> Planner
    CoreInit --> Graph
    CoreInit --> Models
    CoreInit --> Providers

    Planner --> Graph
    Planner --> Models
    Planner --> Providers

    SL_Adapters -.implements.-> Providers
    SL_Adapters --> Planner
    SL_Routes --> SL_Adapters

    Custom_Provider -.implements.-> Providers
    Custom_Provider --> Planner

    Demo --> CoreInit
    Tests --> CoreInit
```
