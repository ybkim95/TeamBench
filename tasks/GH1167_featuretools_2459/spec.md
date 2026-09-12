# GH1167_featuretools_2459: Fix bug with `NumWords`; add test suite — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2457
- Repo: https://github.com/alteryx/featuretools

## Issue Description

```
 NumWords().get_function()(pd.Series(["hello   world"]))
```
Returns 4. Adding another space would return 5. 

The issue is with how the number of words is counted. Consecutive spaces should be collapsed into one.

## PR Review Comments

**[user]** on `featuretools/primitives/standard/transform/natural_language/num_words.py`:

We should decide what to return given null input. Prior to this change, we returned 0 given null input. However, some of our other primitives return null given null input. If we choose to return null, we should update `NumCharacters` as well to keep the primitives uniform.  

The return type of the primitive should be updated to reflect this decision if needed.

**[user]** on `docs/source/release_notes.rst`:

Add your username here.

**[user]** on `featuretools/primitives/standard/transform/natural_language/num_words.py`:

I think we are sort of dividing this primitive logic up between the `word_counter` function and the `_get_number_of_words` function by splitting on `DELIMTERS` before calling `.apply`.

Can we refactor this to call `.apply` on the original series, and add the logic for splitting on `DELIMITERS` to the _get_number_of_words` function instead?

Maybe something like this:
```
    def get_function(self):
        def word_counter(array):
            def _get_number_of_words(elem):
                """Returns the number of words or null given non-iterable input"""
                if not isinstance(elem, str):
                    return pd.NA
                return sum(1 for word in re.split(DELIMITERS, elem) if word.strip(punctuation))

            return array.apply(_get_number_of_words)

        return word_counter
```

**[user]** on `featuretools/primitives/standard/transform/natural_language/num_words.py`:

Do you need the `len()` check here or is it enough to check on the truthy value of a string?

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_num_words.py`:

is `TEST,test` considered one word here? Is that really what we want?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
