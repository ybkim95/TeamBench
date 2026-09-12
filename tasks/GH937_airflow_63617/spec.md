# GH937_airflow_63617: Fix zip DAG import errors being cleared during bundle refresh — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

Bundle refresh cleanup was treating ZIP archives as if only the outer archive path existed. Import errors for DAGs inside a ZIP are stored with inner paths such as test_zip.zip/broken_dag.py, but the observed file set only contained test_zip.zip. As a result, clear_orphaned_import_errors() could incorrectly delete still-valid import errors for broken DAGs inside ZIP archives. 

<!-- SPDX-License-Identifier: Apache-2.0
      https://www.apache.org/licenses/LICENSE-2.0 -->

<!--
Thank you for contributing!

Please provide above a brief description of the changes made in this pull request.
Write a good git commit message following this guide: http://chris.beams.io/posts/git-commit/

Please make sure that your code changes are covered with tests.
And in case of new features or big changes remember to adjust the documentation.

Feel free to ping (in general) for the review if you do not see reaction for a few days
(72 Hours is the minimum reaction time you can expect from volunteers) - we sometimes miss notifications.

In case of an existing issue, reference it using one of the following:

* closes: #ISSUE
* related: #ISSUE
-->

---

##### Was generative AI tooling used to co-author this PR?

<!--
If generative AI tooling has been used in the process of authoring this PR, please
change below checkbox to `[X]` followed by the name of the tool, uncomment the "Generated-by".
-->

- [X] Yes (please specify the tool below)
  Yes used for tests using copilot

<!--
Generated-by: [Tool Name] following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)
-->

---

* Read the **[Pull Request Guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#pull-request-guidelines)** for more information. Note: commit author/co-author name and email in commits become permanently public when merged.
* For fundamental code changes, an Airflow Improvement Proposal ([AIP](https://cwiki.apache.org/confluence/display/AIRFLOW/Airflow+Improvement+Proposals)) is needed.
* When adding dependency, check compliance with the [ASF 3rd Party License Policy](https://www.apache.org/legal/resolved.html#category-x).
* For significant user-facing changes create newsfragment: `{pr_number}.significant.rst`, in [airflow-core/newsfragments](https://github.com/apache/airflow/tree/main/airflow-core/newsfragments). You can add this file in a follow-up commit after the PR is created so you know the PR number.

## PR Review Comments

**[user]** on `airflow-core/src/airflow/dag_processing/manager.py`:

`_get_observed_filelocs(found_files)` opens and reads every zip archive in the bundle. But `deactivate_deleted_dags` (line 694) also calls `_get_observed_filelocs` internally with the same `found_files` set (see line 748). So each zip gets opened and scanned twice per refresh cycle.

You could compute the result once here and pass it into both `deactivate_deleted_dags` and `clear_orphaned_import_errors`.

**[user]** on `airflow-core/src/airflow/dag_processing/manager.py`:

This calls `_get_observed_filelocs(present)` but the caller (`_refresh_dag_bundles`) already calls it with the same `found_files` on line 697. Consider accepting the pre-computed `observed_filelocs` as a parameter instead, so the zip expansion happens only once per bundle.

**[user]** on `airflow-core/src/airflow/dag_processing/manager.py`:

make sense ;)

**[user]** on `airflow-core/src/airflow/dag_processing/manager.py`:

nit: The old `find_zipped_dags` had a docstring explaining it yields absolute paths formed by joining the inner ZIP path with the ZIP file path. That got dropped in the move to `_get_observed_filelocs`. A short docstring like `"""Yield absolute paths for DAG-like files inside a ZIP archive."""` would help readers understand what the yielded values represent.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
