# GH930_mlflow_1758: Fix [SETUP-BUG] #1748 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

## What changes are proposed in this pull request?
 
This patch fixes a setup issue with creating new MLflow instance with MS
SQL server.
 
## How is this patch tested?
 
Tested with MS Azure. Deployed as Docker image using Azure Kubernetes Services with Azure SQL database.
 
## Release Notes
 
Support using MS SQL Server database when creating new instances of MLflow. Setting that enables adding a `experiment_id = 0` for auto increment column.
 
### What component(s) does this PR affect?
 
- [ ] Serving

### How should the PR be classified in the release notes? Choose one:
 
- [X] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes

## PR Review Comments

**[user]** on `mlflow/store/sqlalchemy_store.py`:

This function now serves different purposes based on database type (eventually to allow adding a row for experiment_id == 0): 
- config letting MySQL override default to allow `0` value for experiment ID (auto increment column)
- config letting MSSQL override default to allow any manual value inserted into `IDENTITY` column

Could you rename these function to `_set_zero_value_insertion_for_autoincrement_column` and `_unset_zero_value_insertion_for_autoincrement_column`. The contents in each of these functions correctly override appropriate configs.

**[user]** on `mlflow/store/sqlalchemy_store.py`:

Thank you for your explanation and instructions. I'll update this pull request accordingly.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
