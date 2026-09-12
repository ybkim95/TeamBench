# DB1_migration_conflict (Brief)

Two feature branches (`feature/payments` and `feature/analytics`) produced conflicting
SQL migrations for the `ShopApp` database. Resolve the conflicts so
all migrations apply cleanly and the final schema is correct.

```bash
python apply_migrations.py schema.db
python verify_schema.py schema.db
```

Both commands must complete without errors.

**Files to work in:** `migrations/`
**Reference:** `migration_policy.md` describes the conflict resolution rules.
**Do NOT modify:** `0001_baseline.sql`, `apply_migrations.py`, `verify_schema.py`

Follow the Planner's guidance precisely.
