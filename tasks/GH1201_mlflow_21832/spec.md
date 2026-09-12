# GH1201_mlflow_21832: Fix flaky test_create_model_version_with_validation_regex by disabling job execution — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

<!--
Do not remove any sections. Remove unused checkboxes except for the patch release section at the bottom.
Use backticks for code references and file paths in the PR title (e.g., `ClassName`, `function_name`, `utils.py`).
-->

### Related Issues/PRs

<!-- 🚨 Choose either "Closes" (auto-close on merge) or "Relates to" (reference only). 🚨 -->

Closes | Relates to #issue_number

### What changes are proposed in this pull request?

  Summary                                                                                                                                                                                                                                           
                                                                                  
  - Disable job execution (MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false) in the subprocess server spawned by test_create_model_version_with_validation_regex                                                                                            
                                                                                  
  Context                                                                                                                                                                                                                                           
                                                                                  
  This test has been failing consistently in scheduled CI since March 17. It spawns an mlflow server subprocess and polls /health with a 10-second timeout. The server starts successfully, but the job execution system (huey consumer launch, temp
   directory setup, environment wiring) adds enough startup overhead that CI runners under load can't become ready in time.
                                                                                                                                                                                                                                                    
  Job execution is not needed for this test — it only validates the model version source regex. Disabling it removes the overhead and brings startup well within the timeout window.                                                                
                                                     
  Same root cause as #20436, which previously addressed this test's flakiness by reducing database migration overhead.  

### How is this PR tested?

- [x] Existing unit/integration tests
- [ ] New unit/integration tests
- [x] Manual tests

Test passes locally still.
<!-- Attach code, screenshot, video used for manual testing here. -->

### Does this PR require documentation update?

- [x] No.
- [ ] Yes. I've updated:
  - [ ] Examples
  - [ ] API references
  - [ ] Instructions

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

<!-- When updating APIs or feature usage, please ensure the MLflow Skills repository reflects those changes. -->

- [x] No.
- [ ] Yes. Please link the corresponding PR or explain how you plan to update it.

<!-- Provide the link to the Skills repository PR or a brief explanation of the changes needed. -->

### Release Notes

#### Is this a user-facing change?

- [x] No.
- [ ] Yes. Give a description of this change to be included in the release notes for MLflow users.

<!-- Details in 1-2 sentences. You can just refer to another PR with a description if this PR is part of a larger change. -->

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [ ] `area/tracking`: Tracking Service, tracking client APIs, autologging
- [ ] `area/models`: MLmodel format, model serialization/deserialization, flavors
- [ ] `area/model-registry`: Model Registry service, APIs, and the fluent client calls for Model Registry
- [ ] `area/scoring`: MLflow Model server, model deployment tools, Spark UDFs
- [ ] `area/evaluation`: MLflow model evaluation features, evaluation metrics, and evaluation workflows
- [ ] `area/gateway`: MLflow AI Gateway client APIs, server, and third-party integrations
- [ ] `area/prompts`: MLflow prompt engineering features, prompt templates, and prompt management
- [ ] `area/tracing`: MLflow Tracing features, tracing APIs, and LLM tracing functionality
- [ ] `area/projects`: MLproject format, project running backends
- [ ] `area/uiux`: Front-end, user experience, plotting, JavaScript, JavaScript dev server
- [x] `area/build`: Build and test infrastructure for MLflow
- [ ] `area/docs`: MLflow documentation pages

<!--
Insert an empty named anchor here to allow jumping to this section with a fragment URL
(e.g. (withheld: the upstream fix is not part of the task)#user-content-release-note-category).
Note that GitHub prefixes anchor names in markdown with "user-content-".
-->

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section
- [ ] `rn/breaking-change` - The PR will be mentioned in the "Breaking Changes" section
- [ ] `rn/feature` - A new user-facing feature worth mentioning in the release notes
- [ ] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes
- [ ] `rn/documentation` - A user-facing documentation change worth mentioning in the release notes

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

<details>
<summary>What is a minor/patch release?</summary>

- Minor release: a release that increments the second part of the version number (e.g., 1.2.0 -> 1.3.0).
  Minor releases are expected to contain larger changes, such as new features and improvements. Non-critical bug fixes and doc updates can be included as well. By default, your PR should target the next minor release.
- Patch release: a release that increments the third part of the version number (e.g., 1.2.0 -> 1.2.1).
  Patch releases are typically only performed when there has been a major regression or bug in the latest release. For the sake of stability, your PR should not be included in a patch release unless it is a critical fix, or if the risk level of your PR is exceedingly low.

</details>

<!-- Do not modify or remove any text inside the parentheses. Keep both checkboxes below. -->

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

## PR Review Comments

**[user]** on `tests/tracking/test_rest_tracking.py`:

🟡 **MODERATE:** The retry loop’s worst-case wait time is much longer than implied by `range(30)` because each attempt can block for up to `timeout=2` seconds and then sleeps for 1 second. In a failure case, this can take ~90s (30 * (2s + 1s)). Consider switching to a single `deadline = time.monotonic() + <total_budget>` loop (and/or reducing sleep) so the total wait is bounded and matches the intended startup budget.

**[user]** on `tests/tracking/test_rest_tracking.py`:

🟡 **MODERATE:** `time.sleep(1)` only happens on exceptions; if `/health` responds with a non-2xx status (e.g., wrong process bound to the port), the loop will busy-spin through all retries without waiting, undermining the purpose of having retries. Consider sleeping (or otherwise pacing retries) when the response is not OK as well.

**[user]** on `tests/tracking/test_rest_tracking.py`:

let's remove the timeout just in case the request actually takes longer than 2s (i'm worried about making this fail)

**[user]** on `tests/tracking/test_rest_tracking.py`:

seems useful, let's do this with some reasonable wait time, like maybe 30s? 45s?

**[user]** on `tests/tracking/test_rest_tracking.py`:

🟡 **MODERATE:** The `deadline` doesn’t actually bound the wait time here because `requests.get(...)` has no timeout; a stalled connect/read can block past the 30s budget (and potentially until the test-level timeout). Consider passing an explicit `timeout` (optionally derived from remaining time) and handling `requests.Timeout` as a retry condition.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
