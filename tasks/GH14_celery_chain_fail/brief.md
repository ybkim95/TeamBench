# GH14: Pipeline Failure Propagation (Brief)

Fix the pipeline so failures in any stage propagate correctly rather than
being silently swallowed.

Currently a bad item in stage 1 causes no visible error — the pipeline
returns as if it succeeded.

Verify with:
```
pytest test_pipeline.py -v
```

**Files to fix:** `pipeline.py`
**Do NOT modify:** `tasks.py` or `test_pipeline.py`

Follow the Planner's guidance precisely.
