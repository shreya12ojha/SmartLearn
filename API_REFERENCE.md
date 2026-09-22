# SmartLearn API Reference

Base URL: `http://127.0.0.1:8000`

---

## 1. Authentication Endpoints

### `POST /api/auth/signup`
Registers a new user and returns a JWT bearer token.
- **Request Body**:
  ```json
  {
    "name": "Alex Student",
    "email": "alex@example.com",
    "password": "Password123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "token": "eyJhbGciOi...",
    "user_id": 1
  }
  ```

### `POST /api/auth/login`
Authenticates existing credentials.
- **Request Body**:
  ```json
  {
    "email": "alex@example.com",
    "password": "Password123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "token": "eyJhbGciOi...",
    "user_id": 1
  }
  ```

---

## 2. Path Planning & Personalization Endpoints

### `GET /api/path-planning/roadmap/{user_id}`
Generates a personalized, prerequisite-gated, budget-constrained roadmap.
- **Headers (Optional)**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  {
    "user_id": 1,
    "weekly_budget": 180,
    "allocated_minutes": 120,
    "remaining_budget": 60,
    "next_topic": {
      "topic_id": 2,
      "topic_name": "Linked Lists",
      "domain": "DSA",
      "difficulty": "Intermediate",
      "order": 2,
      "status": "SCHEDULED",
      "mastery_score": 0.4,
      "mastery_level": "Intermediate",
      "estimated_duration": 60,
      "is_unlocked": true,
      "reason": "Scheduled for this week: All prerequisites satisfied (Arrays). Mastery (40%) is below 75% threshold.",
      "blocking_prerequisites": [],
      "satisfied_prerequisites": ["Arrays"]
    },
    "roadmap": [
      {
        "topic_id": 1,
        "topic_name": "Arrays",
        "domain": "DSA",
        "difficulty": "Beginner",
        "order": 1,
        "status": "MASTERED",
        "mastery_score": 0.9,
        "mastery_level": "Advanced",
        "estimated_duration": 30,
        "is_unlocked": true,
        "reason": "Mastered: score of 90% meets or exceeds the 75% threshold.",
        "blocking_prerequisites": [],
        "satisfied_prerequisites": []
      },
      {
        "topic_id": 2,
        "topic_name": "Linked Lists",
        "status": "SCHEDULED",
        "mastery_score": 0.4
      },
      {
        "topic_id": 3,
        "topic_name": "Trees",
        "status": "BLOCKED",
        "mastery_score": 0.1,
        "reason": "Blocked: requires mastery of Linked Lists (40% < 75%).",
        "blocking_prerequisites": ["Linked Lists (40% < 75%)"]
      }
    ],
    "summary": {
      "total_topics": 3,
      "scheduled_count": 1,
      "mastered_count": 1,
      "blocked_count": 1,
      "deferred_count": 0
    }
  }
  ```

### `GET /api/path-planning/next-topic/{user_id}`
Returns only the next actionable topic for the student.
- **Response (200 OK)**:
  ```json
  {
    "user_id": 1,
    "next_topic": {
      "topic_id": 2,
      "topic_name": "Linked Lists",
      "difficulty": "Intermediate",
      "estimated_duration": 60,
      "status": "SCHEDULED"
    },
    "reason": "Prerequisites satisfied and current mastery (40%) is below the 75% threshold."
  }
  ```

---

## 3. CMAB / LinUCB Recommendation Endpoints

### `GET /api/recommendations/resource`
Computes LinUCB scores across all 4 formats (`video`, `text`, `practice`, `interactive`) using the 7-dimensional context vector and returns the top format along with a matching learning resource.
- **Query Parameters**:
  - `user_id` (int, required): Student ID
  - `topic_id` (int, required): Topic ID
- **Response (200 OK)**:
  ```json
  {
    "topic_id": 2,
    "topic_name": "Linked Lists",
    "selected_arm": "practice",
    "resource": {
      "id": 12,
      "topic_id": 2,
      "title": "LeetCode: Reverse Linked List Hands-on Practice",
      "url": "https://leetcode.com/problems/reverse-linked-list/",
      "format": "practice",
      "estimated_time": 45,
      "difficulty": "medium"
    },
    "ucb_score": 0.7142,
    "exploration_bonus": 0.3930,
    "context_features": {
      "current_mastery": 0.4,
      "normalized_budget": 0.3,
      "is_pref_video": 0.0,
      "is_pref_text": 0.0,
      "is_pref_practice": 1.0,
      "is_pref_interactive": 0.0,
      "topic_difficulty": 0.66
    },
    "interaction_id": 45
  }
  ```

### `POST /api/recommendations/feedback`
Submits post-quiz learning feedback to update the LinUCB model parameters ($A_a \leftarrow A_a + x x^T$ and $b_a \leftarrow b_a + r x$) with row-level transaction safety.
- **Request Body**:
  ```json
  {
    "user_id": 1,
    "topic_id": 2,
    "selected_arm": "practice",
    "pre_mastery": 0.40,
    "post_mastery": 0.85
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "reward": 0.45,
    "pre_mastery": 0.40,
    "post_mastery": 0.85,
    "arm": "practice",
    "message": "LinUCB model updated for arm 'practice' with reward +0.450"
  }
  ```

---

## 4. Learning Resources Listing

### `GET /api/resources`
Lists learning resources, optionally filtered by `topic_id` and `format`.
- **Query Parameters**:
  - `topic_id` (int, optional): Filter by topic
  - `format` (string, optional): Filter by format (`video`, `text`, `practice`, `interactive`)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "topic_id": 2,
      "title": "Python Loops & Iteration Deep Dive",
      "url": "https://www.youtube.com/watch?v=...",
      "format": "video",
      "estimated_time": 25,
      "difficulty": "easy"
    }
  ]
  ```

---

## 5. Quiz & Assessment Endpoints

### `GET /api/quiz?topic={topic_id}`
Returns quiz questions for the specified topic.
- **Response (200 OK)**:
  ```json
  {
    "questions": [
      {
        "id": 10,
        "question_text": "What is the time complexity to insert a node at the head of a Singly Linked List?",
        "options": {
          "A": "O(1)",
          "B": "O(n)",
          "C": "O(log n)",
          "D": "O(n^2)"
        }
      }
    ]
  }
  ```

### `POST /api/quiz/submit`
Submits answers, scores the quiz with difficulty weighting, updates student mastery in the database, and returns mastery scores plus question results.
- **Request Body**:
  ```json
  {
    "user_id": 1,
    "quiz_type": "checkpoint",
    "answers": [
      {
        "question_id": 10,
        "selected_option": "A"
      }
    ]
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "mastery": {
      "2": 0.85
    },
    "results": [
      {
        "question_id": 10,
        "question_text": "What is the time complexity to insert a node at the head of a Singly Linked List?",
        "selected_option": "A",
        "correct_option": "A",
        "is_correct": true
      }
    ]
  }
  ```

### `GET /api/quiz/topics/graph`
Returns all topics and prerequisite pairs in the database.

---

## 6. Assessment Overview Endpoint

### `GET /api/assessment/mastery/{user_id}`
Returns the mastery history and current scores across all attempted topics.
- **Response (200 OK)**:
  ```json
  {
    "user_id": 1,
    "mastery": [
      {
        "topic_id": 1,
        "topic_name": "Arrays",
        "mastery_score": 0.90,
        "mastery_level": "Advanced",
        "last_updated": "2026-09-21T10:00:00"
      }
    ]
  }
  ```
