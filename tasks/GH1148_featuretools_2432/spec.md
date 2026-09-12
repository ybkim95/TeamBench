# GH1148_featuretools_2432: Fix serialization of `word_set` in `NumberOfCommonWords` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2428
- Repo: https://github.com/alteryx/featuretools

## Issue Description

If I use a custom word set for the `NumberOfCommonWords`, and generate a feature for it, I can not serialize it. 

```
from featuretools.feature_base.features_serializer import save_features
common_word_set = {"hi", "my"}
num_common_words = NumberOfCommonWords(word_set=common_word_set) 
fm, fd = ft.dfs(entityset=es, target_dataframe_name="df", trans_primitives=[num_common_words])
feat = fd[-1]
save_features([feat]) 
```

Resolving this issue likely involves converting the set to a JSON serializable format like a list.

## PR Review Comments

**[user]** on `featuretools/primitives/utils.py`:

cant you compare class objects directly?

**[user]** on `featuretools/primitives/utils.py`:

fixed!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
