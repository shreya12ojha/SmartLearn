# SmartLearn: Worked Step-by-Step Example

This document walks through a complete, concrete learning scenario demonstrating:
1. Prerequisite gating with the **75%** threshold.
2. Weekly budget allocation.
3. LinUCB contextual recommendation and mathematical updates.
4. Downstream topic unlocking.

---

## 1. Scenario Definition

### Curriculum Graph
```
Arrays (Beginner, 30m)
   ↓
Linked Lists (Intermediate, 60m)
   ↓
Trees (Advanced, 90m)  ←  Recursion (Intermediate, 60m)
```
- **Prerequisite Rules**:
  - `Linked Lists` requires `Arrays`.
  - `Trees` requires **both** `Linked Lists` AND `Recursion`.
- **Student Profile**:
  - Weekly Time Budget: **180 minutes**
  - Preferred Format: **practice**

### Initial Student Mastery Scores
| Topic | Mastery Score | Mastery Tier | Status relative to 75% Threshold |
| :--- | :--- | :--- | :--- |
| **Arrays** | 90% (0.90) | Advanced | $\ge 75\%$ (Mastered) |
| **Recursion** | 80% (0.80) | Advanced | $\ge 75\%$ (Mastered) |
| **Linked Lists** | 35% (0.35) | Beginner | $< 75\%$ (Needs Study, Unlocked) |
| **Trees** | 10% (0.10) | Beginner | $< 75\%$ (Blocked by Linked Lists) |

---

## 2. Step 1: Path Planning Agent Execution

The planner performs topological sorting using Kahn's algorithm:
`[Arrays, Recursion, Linked Lists, Trees]`

1. **Arrays**:
   - Score: $0.90 \ge 0.75$
   - Status: `MASTERED` (0 minutes allocated).
2. **Recursion**:
   - Score: $0.80 \ge 0.75$
   - Status: `MASTERED` (0 minutes allocated).
3. **Linked Lists**:
   - Score: $0.35 < 0.75$
   - Prerequisites check: `Arrays` ($0.90 \ge 0.75$) $\to$ **Satisfied!**
   - Budget check: $0 + 60\text{m} \le 180\text{m}$ $\to$ Fits!
   - Status: `SCHEDULED` (60 minutes allocated).
   - Marked as **Next Recommended Topic**.
4. **Trees**:
   - Score: $0.10 < 0.75$
   - Prerequisites check: `Linked Lists` ($0.35 < 0.75$) $\to$ **Blocked!**
   - Status: `BLOCKED`.

**Summary**:
- Allocated: 60 minutes.
- Remaining Budget: 120 minutes.
- Next Topic: **Linked Lists**.

---

## 3. Step 2: LinUCB Format Recommendation

Student is about to study **Linked Lists**. The system queries `LinUCBBanditService`.

### Context Vector ($x \in \mathbb{R}^7$)
- $x[0]$ (Current Mastery): $0.35$
- $x[1]$ (Normalized Budget): $180 / 600 = 0.30$
- $x[2]$ (`is_pref_video`): $0.0$
- $x[3]$ (`is_pref_text`): $0.0$
- $x[4]$ (`is_pref_practice`): $1.0$
- $x[5]$ (`is_pref_interactive`): $0.0$
- $x[6]$ (Difficulty): $0.66$ (Intermediate)

$$x = [0.35, 0.30, 0.0, 0.0, 1.0, 0.0, 0.66]^T$$

### Initial Scoring (prior to learning history)
With initial $A_a = I_7$ and $b_a = 0_7$:
$$\theta_a = A_a^{-1} b_a = 0$$
$$\text{Mean} = \theta_a^T x = 0$$
$$\text{Variance} = x^T I_7 x = \|x\|^2 = 0.35^2 + 0.30^2 + 1.0^2 + 0.66^2 = 0.1225 + 0.09 + 1.0 + 0.4356 = 1.6481$$
$$\text{Bonus} = \alpha \sqrt{1.6481} = 0.5 \times 1.2838 = 0.6419$$
$$p_a = 0.0 + 0.6419 = 0.6419$$

The bandit selects an exploratory arm (or the student's preference format `practice` when tied).
Matched Resource:
- Title: *"LeetCode: Reverse Linked List Hands-on Practice"*
- Format: `practice`
- Est. Time: 45 minutes

---

## 4. Step 3: Student Study & Quiz Submission

1. **Pre-Mastery Captured**:
   $$\text{pre\_mastery} = 0.35$$

2. **Student Takes Linked Lists Quiz**:
   - Submits 3 questions to `POST /api/quiz/submit`.
   - Answers are scored with difficulty weights.
   - Student gets all 3 questions correct.

3. **Backend Updates Database**:
   - `QuizAttempt` created with score $1.00$.
   - `MasteryScore` for (user, Linked Lists) updated to $1.00$ (Advanced).
   $$\text{post\_mastery} = 1.00$$

---

## 5. Step 4: Reward Calculation & Bandit Update

1. **Authoritative Reward**:
   $$r = \text{post\_mastery} - \text{pre\_mastery} = 1.00 - 0.35 = +0.650$$

2. **LinUCB Update Dispatched**:
   `POST /api/recommendations/feedback`
   - Arm: `practice`
   - Reward: $+0.650$

3. **Transaction-Safe Database Update**:
   - Exclusive row lock acquired on `bandit_model_state` for arm `practice`.
   - Matrix update:
     $$A_{\text{practice}} \leftarrow A_{\text{practice}} + x x^T$$
   - Vector update:
     $$b_{\text{practice}} \leftarrow b_{\text{practice}} + 0.650 \cdot x$$
   - Transaction committed and lock released.

---

## 6. Step 5: Dynamic Downstream Unlocking

The student reloads the Roadmap:

| Topic | New Mastery Score | Prerequisite Check | New Status |
| :--- | :--- | :--- | :--- |
| **Arrays** | 0.90 | None | `MASTERED` |
| **Recursion** | 0.80 | None | `MASTERED` |
| **Linked Lists** | **1.00** | Arrays (0.90 $\ge$ 0.75) | `MASTERED` |
| **Trees** | 0.10 | Linked Lists (1.00 $\ge$ 0.75) AND Recursion (0.80 $\ge$ 0.75) $\to$ **ALL SATISFIED!** | **`SCHEDULED`** |

**Result**:
- **`Trees` is immediately UNLOCKED and becomes the Next Recommended Topic!**
- Allocated: 90 minutes.
- Remaining Budget: 90 minutes.
