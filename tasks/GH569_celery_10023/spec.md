# GH569_celery_10023: reliable prefork detection — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

Fixes https://github.com/celery/celery/discussions/10018#discussioncomment-15209745 as (withheld: the upstream fix is not part of the task) is not reliable for CLI.

Tested locally for `-P threads`, `-P prefork`, _without -P (default fallback)_ and the prefork detection works as intended now.

But I don't like the class interface changes as it could be breaking in any downstream code. But couldn't find any other way. If there is better way, guidance is welcome.

If there will be agreement with current solution I can continue with work on failing tests (the worker instance must be newly passed).

## PR Review Comments

**[user]** on `celery/fixups/django.py`:

why the self.db_reuse_max is being removed?

**[user]** on `celery/fixups/django.py`:

The removal of the `self.db_reuse_max` assignment in `__init__` appears to be unintentional, as it's still referenced in the `close_database` method at lines 199 and 201. This will cause an `AttributeError` when `close_database` is called. Is this intended?
- If yes: The `db_reuse_max` attribute needs to be set somewhere (perhaps as a property that reads from `self.app.conf.get('CELERY_DB_REUSE_MAX', None)`), or the logic in `close_database` needs to be updated.
- If no: Should we restore the line `self.db_reuse_max = self.app.conf.get('CELERY_DB_REUSE_MAX', None)` after line 129?

**[user]** on `celery/fixups/django.py`:

This appears to be a backward-compatibility breaking change: the `DjangoWorkerFixup.__init__` signature now requires a `worker` parameter. Is this intended?
- If yes: Could we add migration guidance in the PR description and docs (versionchanged::), and consider a compatibility approach (e.g., making `worker` optional with a default of `None` and handling that case gracefully) through the next major version?
- If no: Should we make the `worker` parameter optional to maintain backward compatibility with existing code that instantiates `DjangoWorkerFixup` directly?

**[user]** on `celery/fixups/django.py`:

The `worker_fixup` property accesses `self.worker` which is `None` until `on_worker_init` is called. However, `on_import_modules` (lines 103-105) calls `self.worker_fixup.validate_models()` before `on_worker_init` has set `self.worker`. This will cause `DjangoWorkerFixup` to be instantiated with `worker=None`, which will lead to an `AttributeError` when line 213 tries to access `self.worker.pool_cls.__module__`. Should we handle the case where `worker` might be `None` in the `worker_fixup` property, or ensure `worker` is set before `on_import_modules` is called?

**[user]** on `celery/fixups/django.py`:

The prefork detection logic `"prefork" in self.worker.pool_cls.__module__` assumes `self.worker` is not `None`. However, there are code paths where `worker` could be `None` (e.g., when `worker_fixup` is accessed before `on_worker_init`). Should we add a safety check here, such as `is_prefork = self.worker and "prefork" in self.worker.pool_cls.__module__` or ensure `worker` is always set before this code is reached?
```suggestion
        is_prefork = self.worker is not None and "prefork" in self.worker.pool_cls.__module__
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
