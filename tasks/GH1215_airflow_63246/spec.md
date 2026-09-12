# GH1215_airflow_63246: fix(providers/alibaba): pass relative path to oss_write in OSSRemoteLogIO.upload — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

## Problem

`OSSRemoteLogIO.upload()` passes a full OSS URI to `oss_write()`, which internally prepends `base_folder` again. This produces malformed keys like `prefix/logs/oss://bucket/prefix/logs/dag_id=.../attempt=1.log`, making logs unreadable from the Airflow UI.

## Root Cause

`upload()` joins `self.remote_base` (the full `oss://bucket/prefix` URI) with the relative path, then passes the result to `oss_write()`. But `oss_write()` already prepends `self.base_folder` (extracted from `remote_base`), so the prefix gets doubled.

## Fix

Pass only the relative path (relative to `base_log_folder`) to `oss_write()` instead of the full OSS URI. Added a test to verify both absolute and relative input paths produce the correct relative argument to `oss_write()`.

Closes: #63242

<!-- SPDX-License-Identifier: Apache-2.0
      https://www.apache.org/licenses/LICENSE-2.0 -->

---

##### Was generative AI tooling used to co-author this PR?

- [X] Yes — Claude Code

Generated-by: Claude Code following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)

---

* Read the **[Pull Request Guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#pull-request-guidelines)** for more information. Note: commit author/co-author name and email in commits become permanently public when merged.
* For fundamental code changes, an Airflow Improvement Proposal ([AIP](https://cwiki.apache.org/confluence/display/AIRFLOW/Airflow+Improvement+Proposals)) is needed.
* When adding dependency, check compliance with the [ASF 3rd Party License Policy](https://www.apache.org/legal/resolved.html#category-x).
* For significant user-facing changes create newsfragment: `{pr_number}.significant.rst`, in [airflow-core/newsfragments](https://github.com/apache/airflow/tree/main/airflow-core/newsfragments). You can add this file in a follow-up commit after the PR is created so you know the PR number.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
