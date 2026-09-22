# Architecture of Path Planning Agent

## Overview

The Path Planning Agent is designed to solve a single fundamental problem:
> **"What should the student study next?"**

It deliberately leaves the question of:
> **"How should the student study that topic?"**

to the Contextual Multi-Armed Bandit (CMAB / LinUCB) layer.

```
+-------------------------------------------------------------+
|                      STUDENT CONTEXT                        |
|   Mastery Scores (0-100%)    Weekly Time Budget (minutes)   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                       CONCEPT GRAPH                         |
|   Topics (Nodes)             Prerequisites (Directed Edges) |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    PATH PLANNING AGENT                      |
|   1. Kahn's Topological Sort                                |
|   2. Mastery Gating (>= 75% threshold)                      |
|   3. Prerequisite Blocking (Block if any prereq < 75%)       |
|   4. Budget Allocation (Schedule within weekly minutes)     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     PERSONALIZED ROADMAP                    |
|   - MASTERED: Topics >= 75%                                 |
|   - SCHEDULED: Unlocked & within time budget               |
|   - BLOCKED: Missing prerequisites (with reasons)           |
|   - DEFERRED: Unlocked but exceeds weekly budget            |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     NEXT ACTIONABLE TOPIC                   |
+-------------------------------------------------------------+
```

## Core Abstractions

1. **`TopicNode`**: Represents a concept with metadata, domain, difficulty, and duration.
2. **`ConceptGraph`**: Directed Acyclic Graph providing topological sorting, cycle detection, and prerequisite checking.
3. **`StudentMastery`**: Normalized continuous mastery level (0.0 to 1.0) and assessment status.
4. **`PathPlanningAgent`**: Domain orchestrator generating `RoadmapResult`.
5. **Providers**:
   - `ConceptGraphProvider`: Fetches the graph structure.
   - `MasteryProvider`: Fetches student mastery.
   - `StudentContextProvider`: Fetches student preferences and weekly time budget.
