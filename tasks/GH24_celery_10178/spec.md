# GH24_celery_10178: Fix mock connection interfaces to prevent `TypeError` during exception handling — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/celery/celery/issues/10177
- Repo: https://github.com/celery/celery

## Issue Description

# Checklist
- [x] I have checked the [issues list](https://github.com/celery/celery/issues?q=is%3Aissue+label%3A%22Issue+Type%3A+Enhancement%22+-label%3A%22Category%3A+Documentation%22)
  for similar or identical enhancement to an existing feature.
- [x] I have checked the [pull requests list](https://github.com/celery/celery/pulls?q=is%3Apr+label%3A%22Issue+Type%3A+Enhancement%22+-label%3A%22Category%3A+Documentation%22)
  for existing proposed enhancements.
- [x] I have checked the [commit log](https://github.com/celery/celery/commits/main)
  to find out if the same enhancement was already implemented in the
  main branch.
- [x] I have included all related issues and possible duplicate issues in this issue
      (If there are none, check this box anyway).

## Related Issues and Possible Duplicates
#### Related Issues

- #10173 
- celery/kombu#2478

#### Possible Duplicates

- None

# Brief Summary
Currently, several unit tests in Celery pass a bare `Mock()` as the broker connection object. This implicitly creates `Mock` instances for properties like `connection_errors` and `channel_errors` instead of the expected `tuple` of exception classes. 

This fragility was recently exposed by Kombu PR #2473, resulting in `TypeError: unsupported operand type(s) for +: 'Mock' and 'Mock'`. This enhancement proposes explicitly defining these attributes as empty tuples `()` on the mock connection objects. This will make the test suite more robust, accurately reflect the Kombu `Connection` contract, and prevent future CI breakages caused by internal Kombu exception-handling changes.

# Design

## Architectural Considerations
None. This strictly improves the internal unit testing suite to better align with Kombu's expected `Connection` interface.

## Proposed Behavior
We will update the mock connection setup in the affected test files (specifically `t/unit/worker/test_bootsteps.py`, `t/unit/worker/test_consumer.py`, and `t/unit/worker/test_worker.py`).

**Current Mock Behavior:**
```python
c = Mock(name='consumer')
c.connection = Mock()
c = Mock(name='consumer')
c.connection = Mock()
c.connection.connection_errors = ()
c.connection.channel_errors = ()
```

By explicitly setting these to empty tuples, any operations on these attributes (like tuple concatenation during exception handling in `kombu.common.ignore_errors)` will execute safely as `() + ()`. If an exception path is legitimately triggered during a test, it will evaluate correctly instead of throwing a confusing Mock related `TypeError`.

## Alternatives
The main alternative is relying solely on lazy evaluation within Kombu (currently proposed in celery/kombu#2478).

However, this leaves the Celery test mocks in an undefined state. If a Celery test ever legitimately triggers an exception path that forces the evaluation of those tuples, it will crash with the exact same TypeError, rather than validating the intended behavior. Fixing the mocks directly is the most robust long-term solution.

## PR Review Comments

**[user]** on `t/unit/worker/test_bootsteps.py`:

PR description says `test_start_stop_shutdown` already had `connection_errors`/`channel_errors` set, but this diff adds them here. Could you update the PR description to match what’s actually changed (or clarify which test previously had them)?

**[user]** on `t/unit/worker/test_bootsteps.py`:

[user] can you please check this suggestion?

**[user]** on `t/unit/worker/test_bootsteps.py`:

I've updated the PR description. 

It incorrectly stated that `test_start_stop_shutdown` already had the mock attributes set. In fact, both `test_start_stop_shutdown` and `test_start_no_consumers` were missing `connection_errors` and `channel_errors`. 

The description has now been updated to accurately reflect that both tests were patched in this PR. Thanks for pointing that out!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
