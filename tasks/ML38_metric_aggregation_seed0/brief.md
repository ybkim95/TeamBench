# ML38: Raw Count CTR Metric Bug (Brief)

## Your Task
Fix `metrics.py` — `compute_ctr()` uses `sum(clicks)/sum(impressions)` (raw counts)
instead of averaging per-session rates.

The **search results** CTR pipeline is vulnerable to Simpson's paradox:
heavy users (many impressions, low CTR) dominate the aggregate, giving misleading comparisons.

## What to Fix
- `metrics.py`: `compute_ctr()` — replace raw count formula with per-session averaging
- `metrics.py`: `compare_groups()` — set `"method": "per_session_average"`

## Success Criteria
- `python check_metrics.py` exits 0
- `compare_groups` reports `method: "per_session_average"`
- Per-session lift correctly shows negative (treatment is worse per session)
