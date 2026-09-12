# GH1214_airflow_64120: Fix Task SDK Connection extras from URI constructor — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

The URI-based constructor builds a Connection from_uri and then copies its to_dict output directly into __dict__. to_dict uses extra_dejson, which returns a dict (deserialized JSON). As a result, the new Connection instance stores extra as a dict instead of a JSON string. Later calls to extra_dejson/to_dict/as_json assume extra is a string and call json.loads, which will raise TypeError when extra is a dict. Any code that uses the new constructor with a URI (especially with query params) and then calls extra_dejson, to_dict, or as_json can crash or mis-encode extras

```
Traceback (most recent call last):
  File "/workspace/airflow/poc_conn_uri.py", line 7, in <module>
    print(conn.extra_dejson)
          ^^^^^^^^^^^^^^^^^
  File "/workspace/airflow/task-sdk/src/airflow/sdk/definitions/connection.py", line 276, in extra_dejson
    extra = json.loads(self.extra)
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.12.12/lib/python3.12/json/__init__.py", line 339, in loads
    raise TypeError(f'the JSON object must be str, bytes or bytearray, '
TypeError: the JSON object must be str, bytes or bytearray, not dict
```

can be reproduced:

```
from airflow.sdk.definitions.connection import Connection

uri = "postgresql://user:pass@localhost:5432/db?foo=bar"
conn = Connection(conn_id="c1", uri=uri)
print("extra type:", type(conn.extra))
print("extra value:", conn.extra)
print(conn.extra_dejson)

```

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
codex

<!--
Generated-by: [Tool Name] following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)
-->

---

* Read the **[Pull Request Guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#pull-request-guidelines)** for more information. Note: commit author/co-author name and email in commits become permanently public when merged.
* For fundamental code changes, an Airflow Improvement Proposal ([AIP](https://cwiki.apache.org/confluence/display/AIRFLOW/Airflow+Improvement+Proposals)) is needed.
* When adding dependency, check compliance with the [ASF 3rd Party License Policy](https://www.apache.org/legal/resolved.html#category-x).
* For significant user-facing changes create newsfragment: `{pr_number}.significant.rst`, in [airflow-core/newsfragments](https://github.com/apache/airflow/tree/main/airflow-core/newsfragments). You can add this file in a follow-up commit after the PR is created so you know the PR number.

## PR Review Comments

**[user]** on `task-sdk/tests/task_sdk/definitions/test_connection.py`:

`conn.extra` is a JSON string produced by `json.dumps(dict(parse_qsl(...)))`. The dict key order follows the URL query parameter order, which is stable here, but asserting exact string equality against a hand-written JSON literal is brittle if anyone reorders the query params in the URI. Consider comparing via `json.loads(conn.extra)` instead, the way `test_from_uri_with_query_params` does it at line 309. Not a blocker, just a durability thing.

**[user]** on `task-sdk/tests/task_sdk/definitions/test_connection.py`:

yeah agree :)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
