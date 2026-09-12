# ML37: A/B Test Ignores Novelty Effect

## Goal
Fix `analyze.py` so the ship decision is based on **steady-state** ER,
not overall lift. Run `python analyze.py` then `python check_ab.py` — both must pass.

## Task
An A/B test for a new **feed_ranking** algorithm shows overall positive lift
in engagement_rate over 21 days. However, the first 5 days are
inflated by the novelty effect. After day 5, the treatment actually
underperforms control.

---

## The Bug: Overall Lift Ignores Novelty Effect

### Background: Novelty Effect in A/B Tests

When users encounter a new UI or algorithm, they engage more simply because
it's new — not because it's better. This "novelty effect" inflates early metrics.
Sound A/B analysis separates:
- **Novelty period** (days 0-4): inflated by novelty boost (+10%)
- **Steady-state period** (days 5+): true algorithmic effect (-2%)

### Data Pattern

| Period | Days | Treatment Effect |
|--------|------|-----------------|
| Novelty | 0-4 | base_ctr + 10% (novelty boost) |
| Steady-state | 5-20 | base_ctr -2% (true effect) |

Overall ER: weighted average → **positive** (novelty dominates pooled mean)
Steady-state ER: **negative** (the algorithm actually hurts)

### Current (Buggy) Code

```python
# BUG: pools all days — novelty period inflates overall_lift
overall_abs, overall_rel = compute_lift(ctrl, trt)
ship_decision = overall_abs > 0   # BUG: decision on overall, not steady-state
results["decision_basis"] = "overall"
```

### Correct Fix

```python
# Correct: separate novelty and steady-state periods
late_ctrl = ctrl[novelty_window:]
late_trt  = trt[novelty_window:]
late_abs, late_rel = compute_lift(late_ctrl, late_trt)

ship_decision = late_abs > 0   # Base decision on steady-state only
results["decision_basis"] = "steady_state"
```

After the fix:
- `ship_decision` = False (steady-state lift is -2%)
- `decision_basis` = "steady_state"
- Overall lift is still reported (for transparency) but doesn't drive the decision

---

## Config
- Experiment: 21 days, novelty window: 5 days
- Base ER: 0.05, novelty boost: +10%, steady-state: -2%

## Deliverables
1. Fixed `analyze.py` with steady-state-based ship decision
2. `ab_results.json` with `decision_basis: "steady_state"` and `ship_decision: false`
3. `python check_ab.py` exits 0
