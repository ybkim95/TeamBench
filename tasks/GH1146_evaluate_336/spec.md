# GH1146_evaluate_336: fix caching — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/huggingface/evaluate/issues/294
- Repo: https://github.com/huggingface/evaluate

## Issue Description

If we first run `metric = evaluate.load("seqeval")` in an environment with network, then run it in an environment without network, then it will fail:

```
FileNotFoundError: Couldn't find a module script at /path/seqeval/seqeval.py. Module 'seqeval' doesn't exist on the Hugging Face Hub either.  
```

(Well, this is the error message from `transformers`. The original error message is caught by `transformers`.)

This is caused by incorrect cache folder name. 

https://github.com/huggingface/evaluate/blob/283a1f07d6360e960b3ae829f2aeca839ce29839/src/evaluate/loading.py#L492

Changing this line into `name=self.name.split('/')[-1],` would make everything work. However, I'm not sure whether this is a common problem or just for me. Also not sure whether this fix will affect other part of the codes.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Indeed, I can reproduce that caching the metric script does not seem to work. Let me look into this!

## PR Review Comments

**[user]** on `src/evaluate/loading.py`:

It will raise if the module is not a metric without trying the other module types here no ?

**[user]** on `src/evaluate/loading.py`:

Good catch, this should have been a `pass`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
