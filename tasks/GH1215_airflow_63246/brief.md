# GH1215_airflow_63246: fix(providers/alibaba): pass relative path to oss_write in OSSRemoteLogIO.upload (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest providers/alibaba/tests/unit/alibaba/cloud/log/test_oss_task_handler.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
