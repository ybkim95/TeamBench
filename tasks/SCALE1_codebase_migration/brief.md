# SCALE1: Codebase Migration (Brief)

The application crashes after the HTTP library was upgraded.
Migrate from `requests` to `httpx` across the entire codebase.
The Planner has the migration guide with breaking changes and false-positive patterns.
Run tests: `python -m pytest app/tests/test_client.py -v`
