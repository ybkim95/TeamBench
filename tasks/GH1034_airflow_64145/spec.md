# GH1034_airflow_64145: Fix FAB DB manager discovery in migration-only contexts — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

This PR fixes a bug where the FABDBManager is not automatically discovered during database migrations in lean environments, such as the Helm migrateDatabaseJob.In these contexts (e.g., worker/migration containers), the call to 
create_auth_manager().get_db_manager() in RunDBManager can fail because it may require an application context or runtime state that is not present. Previously, this failure was unhandled, causing the FABDBManager to be skipped and results in missing FAB tables (like ab_user, ab_role) unless manually configured.

This change wraps the fallback auth manager check in a try...except block, ensuring the migration process correctly uses the FABDBManager discovered via ProvidersManager which is the reliable discovery path in these environments.

closes: #63847

Was generative AI tooling used to co-author this PR?

Yes — Gemini (Code Research and PR Description)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
