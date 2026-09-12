# ML38: CTR Uses Raw Counts Instead of Per-Session Rates

## Goal
Fix `metrics.py` so `compute_ctr()` and `compare_groups()` use **per-session averaging**
instead of raw aggregate counts. Run `python simulate.py` then `python check_metrics.py`.

## Task
A recommendation panels Recommendation Click Rate pipeline computes `sum(clicks) / sum(impressions)`
across all sessions. This is vulnerable to Simpson's paradox — sessions with many
impressions dominate the aggregate and can reverse the true effect direction.

---

## The Bug: Raw Aggregate CTR

### Background: Per-Session vs. Raw-Count Aggregation

**Raw count** (buggy): `CTR = Σ clicks_i / Σ impressions_i`
- Dominated by sessions with many impressions (heavy users)
- If heavy users have low CTR, the aggregate is pulled down
- Gives incorrect relative comparisons between groups with different session-length distributions

**Per-session average** (correct): `CTR = mean(clicks_i / impressions_i)`
- Equal weight to each session regardless of length
- Matches user-level experience
- Correct for hypothesis testing (session is the unit of randomization)

### Simpson's Paradox Example

| Segment | RCR | Impressions/session |
|---------|-----|-----|
| Heavy users (12%) | 5.00% | 40-150 |
| Normal users (88%) | 20.00% | 5-20 |

If treatment group has more heavy users, raw CTR can appear **higher** even if
the algorithm is **worse** for every user segment individually.

### Current (Buggy) Code

```python
def compute_ctr(session_clicks, session_impressions):
    total_clicks = sum(session_clicks)
    total_impressions = sum(session_impressions)
    return total_clicks / total_impressions  # BUG: dominated by heavy sessions
```

### Correct Fix

```python
def compute_ctr(session_clicks, session_impressions):
    per_session = [c / i for c, i in zip(session_clicks, session_impressions) if i > 0]
    return float(np.mean(per_session))  # Equal weight per session
```

Also update `compare_groups()` to set `"method": "per_session_average"`.

---

## Config
- 2500 sessions per group, 12% heavy users
- Heavy: 40-150 impressions @ 5.0% CTR
- Normal: 5-20 impressions @ 20.0% CTR

## Deliverables
1. Fixed `metrics.py` with per-session `compute_ctr()` and updated `compare_groups()`
2. `simulation_results.json` showing Simpson's paradox
3. `python check_metrics.py` exits 0
