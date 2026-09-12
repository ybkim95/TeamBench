# GH1180_mlflow_22000: Fix `GatewayStartEvent` to fire at startup instead of shutdown — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### Related Issues/PRs

N/A

### What changes are proposed in this pull request?

The `@record_usage_event(GatewayStartEvent)` decorator on the `gateway start` CLI command only records the telemetry event in its `finally` block — after the wrapped function returns. Since `run_app()` is a blocking call that runs indefinitely (watching for config changes), the event was only recorded when the gateway **shut down**, not when it started. The `duration_ms` also incorrectly captured the entire gateway uptime.

This PR replaces the decorator with a direct `_record_event()` call before `run_app()` so the event fires immediately at startup. The test is updated to verify the event is recorded before `run_app` is called.

### How is this PR tested?

- [x] Existing unit/integration tests

### Does this PR require documentation update?

- [x] No.

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

- [x] No.

### Release Notes

#### Is this a user-facing change?

- [x] No.

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [x] `area/gateway`: MLflow AI Gateway client APIs, server, and third-party integrations

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
