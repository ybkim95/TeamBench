# GH12: CLI Flag Envvar Bug (Brief)

Fix the CLI tool so setting the dry-run environment variable to `false` or `0`
actually disables dry-run mode.

Currently the envvar is always treated as `True` regardless of its value.

Verify with:
```
pytest test_cli.py -v
```

**Files to fix:** `cli.py`
**Do NOT modify:** `config.py` or `test_cli.py`

Follow the Planner's guidance precisely.
