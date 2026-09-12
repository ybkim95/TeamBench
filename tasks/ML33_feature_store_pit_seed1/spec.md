# ML33: Feature Store Point-in-Time Leakage (≤ vs <)

## Goal
Fix `feature_store.py` so the point-in-time join uses strict `<` instead of `<=`.
Run `python train.py` then `python check_store.py` — both must pass.

## Task
Building a **transaction fraud detection with real-time feature store** pipeline.
Features: ['txn_velocity', 'avg_amount', 'device_score', 'location_risk', 'balance_ratio']

At prediction time, feature values must be fetched from the feature store
as they existed BEFORE the label event, not AT the event.

---

## The Bug: Point-in-Time Join Uses `<=` Instead of `<`

**Location**: `get_features_at()` in `feature_store.py`

### Background: Point-in-Time Correctness

A feature store stores time-stamped snapshots of computed features.
At training time, for each label event at `event_ts`, you must join
to the feature snapshot that was available BEFORE the event:

```
Timeline:
  ts=100: feature snapshot A (credit_score=0.5, ...)
  ts=200: feature snapshot B (credit_score=0.8, ...)  ← computed from event data?
  ts=200: LABEL EVENT (default=1)
  ts=300: feature snapshot C (credit_score=0.7, ...)
```

With `<=`: returns snapshot B at ts=200 — may encode event outcome.
With `<`: returns snapshot A at ts=100 — safe, computed before event.

### Current (Buggy) Code

```python
available = entity_rows[entity_rows["ts"] <= event_ts]  # BUG
```

### Correct Fix

```python
available = entity_rows[entity_rows["ts"] < event_ts]   # strict <
```

Also update `check_pit_correctness()`:
```python
return {"uses_strict_lt": True, "operator": "<"}
```

### Impact

| Operator | Includes same-ts features? | Risk |
|----------|---------------------------|------|
| `<=` (bug) | Yes | Label leakage if features computed from event |
| `<` (fix)  | No  | Safe — only truly prior features |

---

## Training Config
- LR: 0.002, Epochs: 38, Batch: 32

## Deliverables
1. Fixed `feature_store.py` with `ts < event_ts` in `get_features_at()`
2. Updated `check_pit_correctness()` returning `uses_strict_lt=True`
3. `training_results.json` after running `python train.py`
4. `python check_store.py` exits 0
