# ML37: A/B Test Novelty Effect Bug (Brief)

## Your Task
Fix `analyze.py` — the ship decision uses overall ER lift,
which is inflated by a novelty effect in the first 5 days.

The new **feed_ranking** algorithm looks positive overall,
but steady-state performance (after day 5) is negative.

## What to Fix
- `analyze.py`: change `ship_decision` from `overall_abs > 0` to `late_abs > 0`
- Set `decision_basis = "steady_state"` in results

## Success Criteria
- `python check_ab.py` exits 0
- `ship_decision = False` (steady-state lift is negative)
- `decision_basis = "steady_state"`
