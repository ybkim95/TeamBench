# GH1047_transformers_16669: Fix example logs repeating themselves — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/transformers

## PR Description

# Fix Loggers repeating themselves during the Examples tests

## What does this add?

This PR refactores slighly how the `stream_handler` is made and passed to `logger` during all of the examples tests

## Why is it needed?

When running the `no_trainer` tests, I was noticing that after each test was called the data would repeat itself. So after test 1 it was only logged once, test 2 twice, etc. 

For example something like the following was printed:
```
***** Running training *****
***** Running training *****
***** Running training *****
  Num examples = 10
  Num examples = 10
  Num examples = 10
```
After further investigation, I found that this was due to the `stream_handler` being added at the start of each test. As discussed in this [SO post I found](https://stackoverflow.com/questions/6729268/log-messages-appearing-twice-with-python-logging), since the loggers are global we keep adding more handlers without actually removing them. 

As a result we kept getting multitudes of sys.stdout loggers being added, leading to these multiple print statements each time. 

The fix is before each test case is written, add in our handler (e.g.):
```python
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class SomeTestCase(TestCasePlus):
  ...
```

Also unsure why this didn't quite happen during CircleCI, but this was what occurred locally for me

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
