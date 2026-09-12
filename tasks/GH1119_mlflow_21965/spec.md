# GH1119_mlflow_21965: Fix flaky `test_backpressure_limits_in_flight_items` by skipping pre-flight trace validation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

`test_backpressure_limits_in_flight_items` (added in #20940) fails intermittently with `assert 5 == 4` because `check_model_prediction` executes a pre-flight call to `predict_fn` *outside* the backpressure semaphore before the evaluation loop starts, inflating the `in_flight` counter by 1. Whether this 5th call completes before the test reads `max_in_flight` is a race condition.

### Evidence

5 CI failures found across recent runs, all showing `assert 5 == 4`:

| Job | Date             | Error           |
| --- | ---------------- | --------------- |
| <a href="https://github.com/mlflow/mlflow/actions/runs/23421916597/job/68128953193">68128953193</a> | 2026-03-23 04:58 | `assert 5 == 4` |
| <a href="https://github.com/mlflow/mlflow/actions/runs/23427437655/job/68145352633">68145352633</a> | 2026-03-23 08:16 | `assert 5 == 4` |
| <a href="https://github.com/mlflow/mlflow/actions/runs/23427398780/job/68145208672">68145208672</a> | 2026-03-23 08:21 | `assert 5 == 4` |
| <a href="https://github.com/mlflow/mlflow/actions/runs/23465468258/job/68276561360">68276561360</a> | 2026-03-23 23:43 | `assert 5 == 4` |
| <a href="https://github.com/mlflow/mlflow/actions/runs/23466288877/job/68278989292">68278989292</a> | 2026-03-24 00:15 | `assert 5 == 4` |

### What changes are proposed in this pull request?

- Set `MLFLOW_GENAI_EVAL_SKIP_TRACE_VALIDATION=true` in `test_backpressure_limits_in_flight_items` to bypass the pre-flight `predict_fn` invocation from `data_validation.py`. The test covers backpressure behavior, not trace validation.
- Added a short inline comment (`# Skip pre-flight predict_fn call that runs outside the backpressure semaphore`) explaining why the env var is needed.

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

- [x] `area/evaluation`: MLflow model evaluation features, evaluation metrics, and evaluation workflows

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

<!-- START COPILOT CODING AGENT TIPS -->
---

💡 You can make Copilot smarter by setting up custom instructions, customizing its development environment and configuring Model Context Protocol (MCP) servers. Learn more [Copilot coding agent tips](https://gh.io/copilot-coding-agent-tips) in the docs.

## PR Review Comments

**[user]** on `tests/genai/evaluate/test_evaluation.py`:

Let's add a comment here on why this is needed.

**[user]** on `tests/genai/evaluate/test_evaluation.py`:

[user] Add a comment explaining why this env var is needed. Something like: `# Skip pre-flight validation call to predict_fn (check_model_prediction) which runs outside the backpressure semaphore and would inflate the in_flight counter.`

**[user]** on `tests/genai/evaluate/test_evaluation.py`:

[user] Add a short inline comment on the line above (line 1575) explaining why we skip trace validation. Keep it to one line, e.g.: `# Skip pre-flight predict_fn call that runs outside the backpressure semaphore`

**[user]** on `tests/genai/evaluate/test_evaluation.py`:

Added in caa6b1f.

**[user]** on `tests/genai/evaluate/test_evaluation.py`:

Added in caa6b1f.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
