# LH2: Budgeted Workflow

## Goal
Complete a multi-step task within a strict command execution budget.

## Hard Requirements

1. Run `python budgeted_task.py` to process data files.
2. The task requires finding and fixing 3 broken data files in `data/`.
3. **Budget**: Maximum 20 command executions total.
4. All 3 data files must be fixed:
   - `data/file_a.json`: has field `"ver"` instead of the required `"version"`. Rename the key to `"version"`.
   - `data/file_b.json`: date `"created"` field is `"2025-06-15T00:00:00"` but must include timezone. Fix to `"2025-06-15T00:00:00Z"`.
   - `data/file_c.json`: has case-insensitive duplicates in `"items"` array -- `"project"/"Project"` and `"query"/"Query"`. Keep only the lowercase version of each.
5. After fixing, run `python validate_all.py` which checks all files.
6. Final output: `output/budget_report.json`
7. `budget_used` must be <= 20.

## Deliverables
- Fixed data files + `output/budget_report.json`.
- Verifier must confirm budget compliance and produce attestation.
