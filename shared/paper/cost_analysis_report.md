# TeamBench Cost-Adjusted Performance Analysis

**Date:** 2026-03-19  
**Data Source:** Phase 3 consolidated results (39 tasks, seeds 1-2, 390 runs)  
**Model:** Gemini 3 Flash Preview  
**Analysis Period:** Full team ablation across 5 conditions

---

## OBJECTIVE

[OBJECTIVE] Assess whether team coordination (planner + executor + verifier) is cost-efficient compared to single-agent baselines, and identify the cost-benefit tradeoff for different orchestration strategies.

---

## DATA SUMMARY

[DATA] 
- **390 total runs** across 39 tasks, 2 seeds (1-2), 5 conditions
- **Conditions:** Oracle (spec-access), Restricted (no-spec), Team-no-plan, Team-no-verify, Full-team
- **Scoring metric:** Partial score (0-1 scale) from secondary evaluation metrics
- **Token estimation method:** Elapsed time (150 tokens/sec throughput assumption)
- **Pricing:** Gemini 3 Flash ($0.10/1M input, $0.40/1M output, 70%/30% split)

---

## KEY FINDINGS

### 1. Performance Ranking by Absolute Score

[FINDING] Full team achieves highest average score, but at escalating cost.

| Condition | Avg Score | Score Distribution | Token Cost | Dollar Cost |
|-----------|-----------|-------------------|------------|------------|
| **full** | **0.8085** | 0.0—1.0 (σ=0.206) | 91,440 | **$0.0174** |
| **team_no_verify** | 0.7691 | 0.0—1.0 (σ=0.236) | 46,185 | $0.0088 |
| **oracle** | 0.6754 | 0.0—1.0 (σ=0.230) | 19,400 | $0.0037 |
| **team_no_plan** | 0.6694 | 0.0—1.0 (σ=0.254) | 34,560 | $0.0066 |
| **restricted** | 0.6289 | 0.0—1.0 (σ=0.229) | 15,510 | $0.0029 |

[STAT:n] 78 runs per condition  
[STAT:effect_size] Full vs Oracle score gap = 0.1332 (19.7% improvement)

### 2. Cost-Efficiency: The Tradeoff

[FINDING] Team coordination is **not cost-efficient** when measured as score-per-dollar spent. Cost increases (4.71x) exceed score gains (1.97x).

| Condition | Score/$ | Score/1M Tokens | Efficiency Rank |
|-----------|---------|-----------------|-----------------|
| **restricted** | **213.43** | 40.55 | ⭐ Best |
| **oracle** | 183.22 | 34.81 | ⭐ 2nd |
| **team_no_plan** | 101.94 | 19.37 | 3rd |
| **team_no_verify** | 87.64 | 16.65 | 4th |
| **full** | 46.54 | 8.84 | ⭐ Worst |

[STAT:effect_size] Full-team efficiency = 0.25x of oracle (1/4 as efficient per dollar)

### 3. Oracle vs. Full Team: The Tradeoff Curve

[FINDING] Full team provides meaningful accuracy gain but at steep cost.

**Performance Metrics:**
- **Score increase:** 0.6754 → 0.8085 (**+0.1332, +19.7%**)
- **Cost increase:** $0.0037 → $0.0174 (**+0.0137, +4.71x**)
- **Efficiency loss:** 183.22 → 46.54 score/$ (**0.25x**)

[STAT:ci] Oracle median score 95% CI: [0.71, 0.73]; Full team 95% CI: [0.86, 0.86]

**Interpretation:**
- If task value aligns with score, full team is optimal (maximize accuracy)
- If cost is critical, oracle or restricted is optimal (maximize efficiency)
- Break-even: Full team justified when 1 point of accuracy is worth ~4.71x cost increase

### 4. Planning and Verification Overhead

[FINDING] Planning adds value; verification adds less.

**Planning (comparing team_no_plan vs. full):**
- Score delta: +0.1391 (+20.8%, from 0.6694 → 0.8085)
- Cost delta: +$0.0108 (+2.48x)
- **Planning ROI:** 12.88 score-points per additional dollar

**Verification (comparing team_no_verify vs. full):**
- Score delta: +0.0394 (+5.1%, from 0.7691 → 0.8085)
- Cost delta: +$0.0086 (+1.98x)
- **Verification ROI:** 4.58 score-points per additional dollar

[STAT:p_value] Planning value ≈ 3x verification value (diminishing returns)

### 5. Token Efficiency Across Conditions

[FINDING] Cost-per-token and score-per-token both degrade with team complexity.

| Condition | Tokens/Run | Cost/Token | Score/1M Tokens |
|-----------|-----------|-----------|-----------------|
| **restricted** | 15,510 | $0.0001897 | 40.55 |
| **oracle** | 19,400 | $0.0001899 | 34.81 |
| **team_no_plan** | 34,560 | $0.0001899 | 19.37 |
| **team_no_verify** | 46,185 | $0.0001900 | 16.65 |
| **full** | 91,440 | $0.0001900 | 8.84 |

**Key insight:** Cost-per-token is constant (~$0.00019/token), but score-per-token halves from restricted (40.55) to full (8.84) because team agents produce more tokens with diminishing marginal returns.

---

## LIMITATIONS

[LIMITATION] 
- **Token estimation:** Conservative lower bound (assumes 150 tokens/sec LLM throughput; actual may be higher if tool-execution overhead dominates, making true LLM efficiency worse than estimated)
- **Pricing assumption:** Based on Gemini 3 Flash list pricing; discounts at scale not modeled
- **Generalization:** Analysis covers 39 tasks (primarily SWE, testing, incident response); results may not generalize to math-heavy, reasoning-intensive, or code-generation-only tasks
- **Input/output split:** 70/30 assumption is approximate; actual distribution varies by task type
- **Single model:** Cross-model cost-efficiency not analyzed (other models may have different cost structures)
- **Task distribution:** Tasks weighted equally; real-world applications may prioritize high-value tasks where team coordination is more justified

---

## RECOMMENDATIONS

### For Benchmark Design
1. **Report cost metrics alongside accuracy** — publish score-per-dollar and score-per-1M-tokens in leaderboards to incentivize efficient solutions
2. **Task-weighted analysis** — group tasks by value/impact and re-run cost-efficiency analysis per group
3. **Cross-model pricing** — extend to GPT-5, Claude 4, open-source models to show how results generalize

### For Production Deployment
1. **Use oracle/restricted for cost-sensitive applications** (183–213 score/$)
2. **Use full team when accuracy is paramount** (accept 0.25x efficiency for +20% accuracy)
3. **Hybrid approach:** Run oracle first, escalate to team only if oracle confidence is low
4. **Selective team deployment:** Use team only for high-value tasks or when partial-success is unacceptable

### For Future Research
1. **Dynamic cost thresholds** — model break-even accuracy value for different task types
2. **Token optimization** — techniques to reduce team communication overhead (summarization, compression)
3. **Parallel team execution** — if planner/executor/verifier can run in parallel, cost multiplier may be 1.5–2x instead of 4.71x

---

## FILES

- **Cost Analysis (JSON):** `/u/ybkim95/TeamBench/shared/paper/cost_analysis.json`
- **Token Analysis (Reference):** `/u/ybkim95/TeamBench/shared/paper/token_analysis.json`
- **Ablation Data (Source):** `/u/ybkim95/TeamBench/shared/ablation_results/phase3_all_consolidated.json`

---

## SUMMARY

**Is team coordination cost-efficient?**

- **Absolute answer:** No. Team is 4x less efficient per dollar (46.54 vs. 183.22 score/$).
- **Qualified answer:** Yes, if you value the +19.7% accuracy gain at ≥4.71x cost. For accuracy-critical systems (safety, compliance), the tradeoff favors teams. For cost-constrained systems (high-volume, low-margin), single agents are optimal.
- **Bottom line:** Teams unlock better performance but at measurable cost. Choose based on task value, not universally.

---

Generated: 2026-03-19 (Scientist agent)
