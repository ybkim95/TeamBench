# GH13: Background Task Blocks Requests (Brief)

Fix the middleware so background tasks don't block other concurrent requests.

Currently a slow background task causes the health-check endpoint to wait
several seconds instead of responding immediately.

Verify with:
```
pytest test_app.py -v
```

**Files to fix:** `middleware.py`
**Do NOT modify:** `app.py` or `test_app.py`

Follow the Planner's guidance precisely.
