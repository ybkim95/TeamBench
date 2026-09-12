# GH1123_airflow_63848: Fix partitioned asset events incorrectly triggering non-partition-aware Dags — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

Partitioned asset events (from DAGs using `CronPartitionTimetable`) were incorrectly
queuing non-partition-aware DAGs in `AssetDagRunQueue`, causing spurious
`ASSET_TRIGGERED` runs. Fixed by skipping the non-partitioned queue path when
`partition_key` is set in `AssetManager._queue_dagruns`.

closes: #63734

---

##### Was generative AI tooling used to co-author this PR?

- [X] Yes — Claude Sonnet 4.6

Generated-by: Claude Sonnet 4.6 following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)

## PR Review Comments

**[user]** on `airflow-core/src/airflow/assets/manager.py`:

This brings up a question the other way around: Should a non-partitioned upstream trigger a partition-aware downstream? I feel the answers should match… It feels a little weird if non-partitioned can trigger partitioned, but partitioned can’t trigger non-partitioned.

**[user]** on `airflow-core/src/airflow/assets/manager.py`:

I may be wrong but isn't this section already handling that? 
https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/assets/manager.py#L385-L395
where it skips partition-aware DAGs when the event has no partition_key.

**[user]** on `airflow-core/src/airflow/assets/manager.py`:

Currently, users can provide a partition key to a non-partition-aware Dag. The main question is how to handle this when triggering downstream partition-aware assets.

One approach is to treat the provided key as a temporary partition context, allowing it to propagate to downstream assets without requiring changes to the upstream Dag. This preserves flexibility, though it's a bit conceptually odd. 

Alternatively, the upstream Dag could be made partition-aware (e.g., set `schedule=PartitionedAssetTimetable(assets=[])`) so keys propagate naturally, but this adds complexity (we'll need to block users from providing partition key to non-partition-aware Dags).

---

I kinda like the first one a bit more. The logic will then be

1. Whether a DagRun can trigger a partitioned aware Dag -> depends on whether the DagRun has a valid partition key
2. Whether a Dag can be triggered by asset events with partition keys -> depends on whether this consumer Dag is partition aware


I think we kinda miss this case during implementation, and assume DagRun with a partition key is always partition aware. might need to check the trigger logic again

**[user]** on `airflow-core/tests/unit/assets/test_manager.py`:

```suggestion
        """partitioned asset events (events with partition key) must not queue non-partition-aware Dags."""
```

**[user]** on `airflow-core/newsfragments/63848.bugfix.rst`:

The whole asset partition thing is a new feature to Airflow and not yet released. so I don't think we need it

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
