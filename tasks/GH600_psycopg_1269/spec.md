# GH600_psycopg_1269: perf: speed up Python UUID converters — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/psycopg/psycopg

## PR Description

Sibling of #1268 (from the same viztracer trace... 😄).

This speeds up the Python UUID dumpers by roughly 20-25% by the benchmark included. (This is significant since there is no Cython speedup for UUID dumping. (I tried implementing that, and it ended up only about 5% faster than these, so possibly not worth it.))

Very negligible speed-up (0-0.2%; could be measurement noise) for the loaders, but still avoiding an extra local.

Same story as in #1268 for `tests/benchmarks/`.

## PR Review Comments

**[user]** on `.pre-commit-config.yaml`:

And why do you want to exclude it?

Either the code in this project respects the quality standard or it doesn't belong to this project.

I don't believe we need to commit a benchmark for this change.

**[user]** on `.pre-commit-config.yaml`:

I couldn't get it to easily behave with the speedup module maybe or maybe not being available. I can remove the benchmark code from this PR.

**[user]** on `psycopg/psycopg/types/uuid.py`:

How can be calling a method on an attribute faster than reading an attribute?

**[user]** on `psycopg/psycopg/types/uuid.py`:

Cute. A micro-benchmark confirms:

```python
>>> timeit.timeit("obj.hex.encode()", "import uuid; obj = uuid.uuid4()")
0.1317441969877109

>>> timeit.timeit("b'%032x' % obj.int", "import uuid; obj = uuid.uuid4()")
0.1017561670159921
```

**[user]** on `psycopg/psycopg/types/uuid.py`:

If you really want to make this any faster, why don't you use the Writebla UUID trick used by the C code?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
