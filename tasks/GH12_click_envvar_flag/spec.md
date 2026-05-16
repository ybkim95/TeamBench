# GH12: Envvar Boolean Flag Always True

## Goal

Fix `cli.py` so the `--dry-run` flag correctly interprets the environment
variable. Currently any non-empty envvar string (including `"false"`, `"0"`,
`"no"`) evaluates to `True` because the code calls `bool(raw_string)`.

## Requirements

1. `DEPLOY_DRY_RUN=false` (or `BACKUP_DRY_RUN=false` / `MIGRATE_DRY_RUN=false`) must produce `dry_run=False`
2. `...=0` must produce `dry_run=False`
3. `...=no` must produce `dry_run=False`
4. `...=true`, `...=1`, `...=yes` must produce `dry_run=True`
5. Absent envvar falls back to the hardcoded default
6. Explicit CLI flag always overrides the envvar
7. All tests in `test_cli.py` pass: `pytest test_cli.py -v`

## Supporting Documents

- `cli.py` — contains the buggy `parse_bool_flag()` function
- `config.py` — configuration loader (correct, do not modify)
- `test_cli.py` — tests

## Contradiction / Hidden Complexity

The bug is subtle: Python's `bool("false")` returns `True` because `"false"`
is a non-empty string. The fix must explicitly parse the string rather than
relying on Python's truthiness rules. A naive agent may miss this and leave
the envvar branch broken.

## Important Notes

- Only `parse_bool_flag()` in `cli.py` needs changing (~1-2 lines)
- Do NOT modify `config.py` or `test_cli.py`
- The fix: `return raw.lower() not in ("0", "false", "no", "")`
