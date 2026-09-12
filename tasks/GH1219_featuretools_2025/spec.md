# GH1219_featuretools_2025: More ordinal comparison fixes — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/alteryx/featuretools

## PR Description

### More ordinal comparison fixes

Implements additional changes to these primitives to enable comparison between ordinal columns that have different order values:
- `GreaterThan`
- `GreaterThanEqualTo`
- `LessThan`
- `LessThanEqualTo`

## PR Review Comments

**[user]** on `featuretools/primitives/standard/binary_transform.py`:

should we have the top level logic be 

```
if val_1 is categorical or val_2 is categorical:
    ....
return val_1 > val_2
```
so that for the non-categorical case we exit after examining one if statement instead of 2?

**[user]** on `featuretools/primitives/standard/binary_transform.py`:

I think we could, but if I'm thinking about this right if we did that the logic might a little harder to follow.

We have a few cases to handle:
1. One input is categorical, the other is not -> `nan`
2. Both inputs are categorical and categories are not equal -> `nan`
3. Both inputs are categorical and categories are equal -> `val1 > val2`
4. Inputs are both numeric or both datetime -> `val1 > val2`

I think if we moved the `or` statement to the top we would have to do something like this and handle the case where they are both equal inside that first conditional:
```python
if val1 is categorical or val2 is categorical:
    if val1 is categorical and val2 is categorical:
        if val1.categories == val2.categories:
            return val1 > val2
    return np.nan
return val1 > val2
```

I guess it's debatable whether that is more clear or less clear, but I find it a little harder to follow. I think the "special case" that should work but doesn't is a little more hidden in the updated flow since it's combined with the case where both are categorical and the categories don't match.

If you prefer that approach I can update - don't have a strong preference. Or is there something better yet that I'm not seeing?

**[user]** on `featuretools/primitives/standard/binary_transform.py`:

What if we keep the if / elif structure but store the `is_categorical` calls in variables so we aren't potentially making them multiple times

**[user]** on `featuretools/primitives/standard/binary_transform.py`:

Sure, we can do that. I was thinking those calls would be pretty fast so didn't worry about it, but maybe that's not the case. Storing in variables certainly won't hurt. I'll update.

**[user]** on `featuretools/primitives/standard/binary_transform.py`:

I think that change will also make the code a little easier to read.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
