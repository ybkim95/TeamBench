# GH1163_mlflow_21808: Fix race condition in `test_job_cancel` causing flaky `test_job_endpoint_search` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### What changes are proposed in this pull request?

Fix for https://github.com/mlflow/mlflow/actions/runs/23247331823/job/67579284333

`test_job_cancel` used `time.sleep(2)` before canceling, but the single Huey worker (`max_workers=1`) may not have started the job yet. Canceling a PENDING job leaves a stale task in the queue; when the worker picks it up, `start_job()` fails with "CANCELED state, cannot start", delaying subsequent jobs and causing `test_job_endpoint_search` to timeout.

- **`tests/server/jobs/test_endpoint.py`**: Replace `time.sleep(2)` with a polling loop that waits up to 20 seconds for `"RUNNING"` status before calling `cancel_job()`. The last observed status is included in the `TimeoutError` message for easier diagnostics:

```python
deadline = time.time() + 20
while time.time() < deadline:
    status = client.get_job(job_id)["status"]
    if status == "RUNNING":
        break
    time.sleep(0.5)
else:
    raise TimeoutError(f"Job did not start running within 20 seconds, last status: {status}")
```

This matches the pattern already used in `tests/server/jobs/test_jobs.py`.

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

- [x] `area/build`: Build and test infrastructure for MLflow

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

<!-- START COPILOT CODING AGENT TIPS -->
---

💬 Send tasks to Copilot coding agent from [Slack](https://gh.io/cca-slack-docs) and [Teams](https://gh.io/cca-teams-docs) to turn conversations into code. Copilot posts an update in your thread when it's finished.

## PR Review Comments

**[user]** on `tests/server/jobs/test_endpoint.py`:

[user] is it possible to include the status in the message?

**[user]** on `tests/server/jobs/test_endpoint.py`:

Done in 1c5384e — the message now reads: `"Job did not start running within 10 seconds, last status: {status}"`

**[user]** on `tests/server/jobs/test_endpoint.py`:

```suggestion
    deadline = time.time() + 30
```

can we increase this to 30?

**[user]** on `tests/server/jobs/test_endpoint.py`:

[user]

**[user]** on `tests/server/jobs/test_endpoint.py`:

Done in 695dd37 — increased to 30 seconds and updated the error message to match.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
