# DEVOPS2_cicd_pipeline: CI/CD Pipeline Bug Fix — Full Specification (Planner Only)

            ## Overview

            The workspace contains a GitHub Actions workflow for a Python project
            (`.github/workflows/ci.yml`) with **5 real configuration bugs** and
            **2 intentional flaky-test patterns** that must be preserved.

            The executor only receives the brief; this spec provides the full analysis.

            ## File Structure

            - `.github/workflows/ci.yml` — the pipeline definition (the ONLY file to modify)
            - `postmortem.md` — incident analysis distinguishing real bugs vs flaky patterns
            - `README.md` — project overview

            ## Real Bugs (Must Be Fixed)

            | # | Type | Current (wrong) | Correct |
            |---|------|-----------------|---------|
            | B1 | wrong_runner_image | `runs-on: ubuntu-20.04` | `runs-on: ubuntu-latest` |
| B2 | missing_env_var | No `env:` block in `Run database migrations` step | Add `env: { DATABASE_URL: ${{ secrets.DATABASE_URL }} }` |
| B3 | wrong_artifact_path | `path: build/` | `path: dist/` |
| B4 | bad_conditional | `if: always()` on deploy step | `if: success() && github.ref == 'refs/heads/production'` |
| B5 | wrong_checkout_depth | `fetch-depth: 1` | `fetch-depth: 0` |

            ### Bug Details

### Bug B1 — EOL Runner Image

**Location:** `runs-on:` in `build-and-test` job

**Root cause:** `ubuntu-20.04` has reached end-of-life and is no longer
maintained. GitHub may remove it at any time, and it lacks security patches.

**Fix:** Change to `runs-on: ubuntu-latest`

### Bug B2 — Missing Environment Variable Injection

**Location:** `Run database migrations` step

**Root cause:** The step runs `python manage.py migrate` which requires
`$DATABASE_URL` to be set, but the step has no `env:` block
to inject the secret. The variable will be empty at runtime, causing
authentication failure.

**Fix:** Add an `env:` block to the step:
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Bug B3 — Wrong Artifact Upload Path

**Location:** `upload-artifact` step, `path:` field

**Root cause:** The `path:` is set to `build/` but the
build step (`pip install -e .`) writes output to `dist/`.
The upload will fail or upload nothing because the wrong directory is referenced.

**Fix:** Change `path: build/` to `path: dist/`

### Bug B4 — Incorrect Step Conditional

**Location:** `Run database migrations` step, `if:` condition

**Root cause:** `if: always()` causes the deploy step to run regardless
of whether previous steps passed or failed. This means a broken build
could be deployed to production.

**Fix:** Change to:
```yaml
if: success() && github.ref == 'refs/heads/production'
```
This ensures deployment only happens on successful runs on the main branch.

### Bug B5 — Shallow Clone Breaks Versioning

**Location:** `Checkout code` step, `fetch-depth:` option

**Root cause:** `fetch-depth: 1` creates a shallow clone without tags.
The build uses `python setup.py --version` which relies on git tags to
determine the version. With a shallow clone, this command fails or
returns a fallback like `0.0.0-unknown`.

**Fix:** Change `fetch-depth: 1` to `fetch-depth: 0` to fetch full
history and all tags.

## Intentional Patterns (DO NOT CHANGE)

### F1 — `continue-on-error: true` on `Run integration tests`

This is **intentional** — the integration tests are known-flaky due to
external service dependencies. The team has explicitly accepted this risk.
Removing `continue-on-error` would cause valid CI runs to fail on transient
network issues.

### F2 — `timeout-minutes: 30` on `Run e2e tests`

This timeout is **correct and intentional** — the test legitimately requires
up to 30 minutes. Reducing it would cause spurious failures.

## Acceptance Criteria

1. All 5 real bugs are fixed in `.github/workflows/ci.yml`
2. `continue-on-error: true` on `Run integration tests` is preserved
3. `timeout-minutes: 30` on `Run e2e tests` is preserved
4. YAML is syntactically valid (`yamllint` reports no errors)
5. Only `.github/workflows/ci.yml` is modified

## Authoritative Sources

- This spec is the authoritative analysis of bugs vs intentional patterns
- `postmortem.md` in the workspace provides the same analysis (readable by agents)
- GitHub Actions documentation is the reference for correct syntax
