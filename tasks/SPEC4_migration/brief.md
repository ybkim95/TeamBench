# SPEC4: Database Schema Migration

A database schema change is needed.  Write the migration script.

- **Workspace**: `database.db` (SQLite), `migration.py` (skeleton)
- **Run**: `python migration.py`
- **Success**: exits 0, prints "Migration complete.", writes `migration_result.json`

The Planner has the full spec with before/after schemas, step order, constraints,
and rollback requirements.
