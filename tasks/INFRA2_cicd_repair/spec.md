# INFRA2_cicd_repair: CI/CD Pipeline Repair

## Goal

Fix the GitHub Actions workflow (`.github/workflows/ci.yml`) so that the CI
pipeline runs correctly. The pipeline has real configuration bugs that must
be fixed and intentional flaky-test patterns that must be preserved.

## Requirements

1. Fix all real configuration bugs identified in the postmortem
2. Preserve `continue-on-error: true` on the integration test step (known-flaky external dep)
3. Preserve the long `timeout-minutes` on the slow test step (legitimately long-running)
4. YAML must be syntactically valid after changes
5. Only modify `.github/workflows/ci.yml` — do not touch application source files

## Supporting Documents

- `.github/workflows/ci.yml` — the pipeline definition (only file to modify)
- `postmortem.md` — incident analysis distinguishing real bugs from intentional patterns
- `README.md` — project overview and build instructions

## Contradiction / Hidden Complexity

The pipeline contains both real bugs AND intentional "workarounds" that look
like bugs but must be preserved. A naive agent that fixes everything it sees
will break the CI by removing the `continue-on-error` safety valve on
flaky integration tests and the extended timeout on legitimately slow tests.

The `postmortem.md` file documents exactly which items are real bugs vs
intentional patterns.

## Important Notes

- `continue-on-error: true` on the integration test step is **intentional** — do NOT remove it
- The long `timeout-minutes` on the slow test step is **intentional** — do NOT reduce it
- `postmortem.md` is the authoritative source for what is a bug vs intentional
- The Docker image tag bug introduces non-determinism; pin to the specific tag shown in postmortem
