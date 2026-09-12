# DS27: Deferred Foreign Key Loading

## Task
Load two tables with **circular foreign key dependencies** into SQLite:
- `projects.kickoff_milestone_id` → `milestones.milestone_id`
- `milestones.project_id` → `projects.project_id`

Data: **11 projects** rows and **17 milestones** rows. 3 rows have deliberate FK violations.

## The Problem
With FK constraints enabled during load, whichever table loads first will fail
because it references a not-yet-populated table. This is the circular dependency problem.

## Solution: Deferred Constraint Checking
1. Disable FK constraints before loading: `PRAGMA foreign_keys = OFF`
2. Load all data (both tables)
3. Re-enable FK constraints: `PRAGMA foreign_keys = ON`
4. Run integrity check to detect violations: `PRAGMA foreign_key_check`

## Data
- `data/projects.csv`: project_id, kickoff_milestone_id, name, value
- `data/milestones.csv`: milestone_id, project_id, name, amount

## Requirements
1. Load both CSVs into SQLite with `PRAGMA foreign_keys = OFF`
2. Load ALL rows from both tables (no silently dropped rows)
3. After loading, enable FK and run `PRAGMA foreign_key_check` to count violations
4. Save to `results.json`:
   - `projects_rows_loaded`: must equal 11
   - `milestones_rows_loaded`: must equal 17
   - `load_errors`: 0 (deferred loading should have no errors)
   - `deferred_fk_used`: `true`
   - `fk_violations_detected`: count from `PRAGMA foreign_key_check`
   - `load_succeeded`: `true`
5. Fix `load_data.py`

## Deliverables
- Fixed `load_data.py`
- `output.db` with all rows loaded
- `results.json`
