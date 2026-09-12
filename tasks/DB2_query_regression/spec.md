# DB2_query_regression: Query Performance Regression Fix

## Goal

Fix query performance regressions caused by a recent schema change. Create
`indexes.sql` containing `CREATE INDEX` statements for queries that genuinely
need indexes. Do NOT add indexes to small tables where sequential scans are
more efficient.

## Requirements

1. Create `indexes.sql` with `CREATE INDEX` statements for the genuine regressions
2. Do NOT create indexes on small reference tables (documented in `dba_analysis.md`)
3. Do NOT create indexes on summary/aggregation tables (full scans are intentional)
4. Index names must follow the format `idx_<table>_<column(s)>`
5. Do NOT modify `schema.sql` or `queries.sql`

## Supporting Documents

- `schema.sql` — database schema with table definitions and row counts
- `queries.sql` — slow queries with EXPLAIN cost annotations
- `dba_analysis.md` — DBA EXPLAIN analysis distinguishing regressions from acceptable scans
- `README.md` — task overview

## Contradiction / Hidden Complexity

Not all slow queries need indexes. Two queries run sequential scans on small
tables where the planner correctly prefers sequential scans over index lookups.
A naive agent that adds indexes to every slow query will add unnecessary overhead
and fail grading.

The `dba_analysis.md` documents exactly which queries need indexes and which
should be left alone, including the DBA rationale.

## Important Notes

- Small reference tables (< 50 rows) with sequential scans are **intentional** — do NOT index them
- Summary/aggregation tables that always do full scans are **intentional** — do NOT index them
- `dba_analysis.md` is the authoritative source for which queries are genuine regressions
- Create the file `indexes.sql` in the workspace root — do not inline SQL into other files
