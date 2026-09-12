# GH424_fastapi_15139: ⬆️ Increase lower bound to `pydantic >=2.9.0.` and fix the test suite — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/fastapi/fastapi

## PR Description

Our CI is intended to test the lowest ranges of our dependency pins as well as the highest, but it turns out this wasn't actually working well for Pydantic, and our lowest "supported" version wasn't actually being tested. Cf more digging by Yurii [here]((withheld: the upstream fix is not part of the task)#discussion_r2943355570).

This PR ensures that the lowest Pydantic supported version is installed when we're testing the lower bounds. From the first commit on this PR, you can see that it fails for the current `master`, which means that we weren't actually supporting the lower versions included in our dependency range.

Some of the issues include:
* AttributeError: Config has no attribute `val_json_bytes` (only introduced in Pydantic 2.9) 
   * This is easily fixed by bumping to lower bound 2.9, solving most issues in one sweep
* Comparison assert failures in `test_schema_pydantic.v2.py`.
   * One is caused by `additionalProperties` being set to `True` always since [Pydantic 2.11](https://github.com/pydantic/pydantic/releases/tag/v2.11.0b1)
   * Bumping to lower bound 2.11 feels a bit much right now, so I've opted to fix these tests instead, allowing multiple versions of the schema.

## PR Review Comments

**[user]** on `tests/test_schema_compat_pydantic_v2.py`:

```suggestion
                    # Pydantic >= 2.11: no top-level OtherRole
```

**[user]** on `tests/test_schema_compat_pydantic_v2.py`:

```suggestion
                    # Pydantic < 2.11: adds a top-level OtherRole schema
```

**[user]** on `.github/workflows/test.yml`:

Not ideal that we duplicate min version number here, but I don't know if we can do better.
And, this should cause any problems. So, I think it's fine

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
