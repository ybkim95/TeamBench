# ML33: Feature Store Point-in-Time Bug (Brief)

## Your Task
Fix the feature store join in `feature_store.py`.

The `get_features_at()` function uses `ts <= event_ts` when looking up features,
which includes features computed at the same timestamp as the label event.
This causes point-in-time leakage when those features encode information from
the event itself.

## What to Fix
- `feature_store.py`: `get_features_at()` — change `<=` to `<` on the ts comparison
- Update `check_pit_correctness()` to return `{"uses_strict_lt": True, "operator": "<"}`
- Do NOT modify `train.py`

## Success Criteria
- `python check_store.py` exits 0
- Features at exact event_ts are excluded from the point-in-time join
