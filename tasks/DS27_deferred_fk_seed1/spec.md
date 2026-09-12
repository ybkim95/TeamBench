# DS27: Deferred Foreign Key Loading

## Task
Load two tables with **circular foreign key dependencies** into SQLite:
- `employees.dept_id` → `departments.dept_id`
- `departments.manager_id` → `employees.employee_id`

Data: **14 employees** rows and **33 departments** rows. 2 rows have deliberate FK violations.

## The Problem
With FK constraints enabled during load, whichever table loads first will fail
because it references a not-yet-populated table. This is the circular dependency problem.

## Solution: Deferred Constraint Checking
1. Disable FK constraints before loading: `PRAGMA foreign_keys = OFF`
2. Load all data (both tables)
3. Re-enable FK constraints: `PRAGMA foreign_keys = ON`
4. Run integrity check to detect violations: `PRAGMA foreign_key_check`

## Data
- `data/employees.csv`: employee_id, dept_id, name, value
- `data/departments.csv`: dept_id, manager_id, name, amount

## Requirements
1. Load both CSVs into SQLite with `PRAGMA foreign_keys = OFF`
2. Load ALL rows from both tables (no silently dropped rows)
3. After loading, enable FK and run `PRAGMA foreign_key_check` to count violations
4. Save to `results.json`:
   - `employees_rows_loaded`: must equal 14
   - `departments_rows_loaded`: must equal 33
   - `load_errors`: 0 (deferred loading should have no errors)
   - `deferred_fk_used`: `true`
   - `fk_violations_detected`: count from `PRAGMA foreign_key_check`
   - `load_succeeded`: `true`
5. Fix `load_data.py`

## Deliverables
- Fixed `load_data.py`
- `output.db` with all rows loaded
- `results.json`
