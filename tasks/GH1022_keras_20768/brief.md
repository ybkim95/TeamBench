# GH1022_keras_20768: fix(ops): Fix issue with map_coordinates for uint8 dtype (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest keras/src/ops/image_test.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
