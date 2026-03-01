# CROSS2: Schema Evolution — Cross-Service Compatibility

## Goal
Service A has been updated with a database migration that modifies the shared schema.
Update Service B to work with the new schema without breaking either service.

## Requirements
1. Update `service_b/models.py` to match the new schema (see `service_a/migrations/002_add_columns.py`)
2. Fix `service_b/queries.py` to use explicit column names (no `SELECT *`)
3. Implement `scripts/backfill.py` to populate new columns for existing records
4. Use default values from `service_a/config.py` for the backfill
5. All tests must pass: `pytest tests/`

## Supporting Documents
- `service_a/migrations/002_add_columns.py` — The migration that changed the schema
- `service_a/config.py` — Default values for new columns
- `shared/schema.sql` — Expected final schema (source of truth)
- `service_b/models.py` — Stale ORM models (need updating)
- `service_b/queries.py` — Contains SELECT * (needs fixing)

## Important
The migration renames one column and adds three new columns. Service B must be updated
to use the new column names. The backfill script must use exact default values from
Service A's config — do not invent values.

## Real-World Context
Column renames silently breaking downstream services are a perennial data engineering
incident:
- **The SELECT * anti-pattern**: When a source table adds or renames columns, any
  downstream `SELECT *` query changes shape invisibly — no error until a consumer
  reads a now-missing field. This pattern caused major outages at Uber (2019) and
  multiple data platform teams documented in Martin Fowler's "Evolutionary Database
  Design" (2016).
- **Expand-Contract migration**: The standard fix — add new column, backfill, update
  consumers, then drop old column — is documented in every major database migration
  guide (Liquibase, Flyway, Alembic). Skipping any step causes exactly the failures
  this task tests.
- **ORM stale model bug**: Django ORM and SQLAlchemy models that reference old column
  names fail silently at query time with `OperationalError: no such column`, not at
  import time — making this class of bug hard to detect in staging.
