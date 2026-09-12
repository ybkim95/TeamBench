# GH43_celery_10155: Improve on_after_finalize signal documentation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/celery/celery/issues/7280
- Repo: https://github.com/celery/celery

## Issue Description

# Checklist
- [X] I have checked the [issues list](https://github.com/celery/celery/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22Category%3A+Documentation%22+)
  for similar or identical bug reports.
- [X] I have checked the [pull requests list](https://github.com/celery/celery/pulls?q=is%3Apr+label%3A%22Category%3A+Documentation%22)
  for existing proposed fixes.
- [X] I have checked the [commit log](https://github.com/celery/celery/commits/master)
  to find out if the bug was already fixed in the master branch.
- [X] I have included all related issues and possible duplicate issues in this issue
      (If there are none, check this box anyway).

## Related Issues and Possible Duplicates

- None

#### Related Issues

- None

#### Possible Duplicates

- None

# Description
<!--
[](https://docs.celeryproject.org/en/stable/reference/celery.html#celery.Celery.on_after_finalize)on_after_finalize
Signal sent after app has been finalized.

This documentation doesn't say more than the name does.  What does it mean when the app has been finalized?  Seems like to Finalize something would be to finish or end it.  But finalize(auto=False) seems to indicated that finalize doesn't have the usual english definition.
-->

# Suggestions
<!-- Please provide us suggestions for how to fix the documentation -->
I'd suggest using finalize in a way that fits with a normal definition but that might be a big ask considering all the existing code and people using it.  So maybe it could just be described better.  Basically I'm trying to use `on_after_configure.connect` and that appears to be too early in the run to be importing things from tasks.py.  So I can here looking to see if I could use `on_after_finalize` based on this page which mentions it, but now I'm not sure what `finalize` means anymore....

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey [user] :wave:,
Thank you for opening an issue. We will get back to you as soon as we can.
Also, check out our [Open Collective](https://opencollective.com/celery) and consider backing us - every little helps!

We also offer priority support for our sponsors.
If you require immediate assistance please consider sponsoring us.

### Comment 2 ([user]):

I'd like to work on this. Updated the docstring and reference docs to explain that finalization evaluates pending task decorators, loads built-in tasks, and binds all tasks to the app — making it the earliest point where the full task registry is available.

PR: #10155

## PR Review Comments

**[user]** on `docs/reference/celery.rst`:

Wording nit for accuracy: `finalize()` evaluates *pending* decorators and binds tasks already registered at that point, but it doesn’t guarantee that every project task module has been imported/autodiscovered yet (and tasks can still be registered after finalization). Could we rephrase “the full task registry is available” to something like “the task registry is initialized/stable and safe to inspect” or “all pending decorators have been evaluated, so registered tasks are bound and can be inspected reliably”?
```suggestion
        and every task registered at that point has been bound to the app.
        At this stage the task registry is initialized and stable enough to
        import and inspect task objects reliably.
```

**[user]** on `celery/app/base.py`:

Minor doc accuracy: `finalize()` binds tasks that are currently registered and flushes pending decorators, but it doesn’t imply the registry contains *all* tasks a project may define (e.g., modules not yet imported/autodiscovered). Consider softening “full task registry is available” to “task registry is initialized/stable and safe to inspect”.
```suggestion
    #: every currently registered task has been bound to the app).  This is
    #: the earliest point at which the task registry is initialized/stable
    #: and safe to inspect for tasks currently registered with this app.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
