# CR4: API Design Fix (Brief)

## Your Task
The REST API in `app.py` was flagged during code review for multiple
API design violations.

Fix all the violations so the API conforms to the team's REST API design guidelines.

## What You Know
- The API is in `app.py` (Flask/Python).
- The code review found issues with: HTTP methods, route naming, pagination,
  status codes, API versioning, and error responses.
- `tests/test_api.py` must pass without any modification after your fixes.
- Do NOT modify `tests/test_api.py`.
- Install dependencies with `pip install -r requirements.txt` before running tests.

## What the Planner Has
The Planner has the full API review report listing every violation with exact
locations and the required fixes. Follow the Planner's instructions precisely.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/test_api.py -v
```
