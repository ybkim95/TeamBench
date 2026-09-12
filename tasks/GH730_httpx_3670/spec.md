# GH730_httpx_3670: Update FileStream API — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/encode/httpx

## PR Description

Fix up server `File` responses...

```python
import httpx

def app(request):
    return httpx.Response(200, content=httpx.File("index.html"))

httpx.run(app)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
