# GH1213_airflow_64216: Fix assume_role_with_web_identity not using botocore config for STS c… (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest providers/amazon/tests/unit/amazon/aws/hooks/test_base_aws.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
