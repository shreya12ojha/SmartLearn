# Synthetic Student Simulation & Regret Evaluation Report

**Simulation Configuration:**
- Total Rounds ($T$): 1000
- Random Seed: 42 (Fixed, deterministic)
- Context Dimension ($d$): 7
- Arms ($K$): 4 (`video`, `text`, `practice`, `interactive`)
- Student Profiles: 4 (`Video Learner`, `Practice Learner`, `Text Learner`, `Interactive Learner`)

---

## 1. Executive Performance Summary

| Metric | LinUCB (CMAB) | Random Baseline | Improvement / Delta |
| :--- | :--- | :--- | :--- |
| **Total Cumulative Reward** | **548.51** | 345.77 | **+58.63%** |
| **Average Reward per Round** | **0.5485** | 0.3458 | **+58.63%** |
| **Cumulative Regret** | **5.39** | 208.12 | **-97.41% (Reduced)** |

---

## 2. Regret Methodology

- **Instantaneous Regret ($r^*_t - r_t$)**: The difference between the maximum expected reward among all 4 arms for the given student profile and topic, and the reward obtained by the chosen arm.
- **Cumulative Regret ($R_T = \sum_{t=1}^T r^*_t - r_t$)**: The accumulated loss from sub-optimal format selections over time.
- **Result**: LinUCB achieves sub-linear regret growth as it rapidly identifies each student's format affinity through exploration-exploitation tradeoff ($lpha = 0.5$).

---

## 3. Arm Selection Distribution

| Learning Format | LinUCB Count | LinUCB Share | Random Count | Random Share |
| :--- | :--- | :--- | :--- | :--- |
| **VIDEO** | 237 | 23.7% | 253 | 25.3% |
| **TEXT** | 234 | 23.4% | 259 | 25.9% |
| **PRACTICE** | 271 | 27.1% | 233 | 23.3% |
| **INTERACTIVE** | 258 | 25.8% | 255 | 25.5% |

---

## 4. Visual Charts

1. **Cumulative Reward**: `simulation/results/cumulative_reward.png`
2. **Cumulative Regret**: `simulation/results/cumulative_regret.png`
3. **Arm Selection Distribution**: `simulation/results/arm_selection_distribution.png`
