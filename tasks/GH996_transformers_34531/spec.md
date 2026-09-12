# GH996_transformers_34531: Fix  #34494 assistant tokens when truncated — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/transformers

## PR Description

This pr fixes a bug that caused  #34494.
when using `apply_chat_template` with `return_assistant_tokens_mask` and token truncation, the assistant mask was not correct.

[user]

## PR Review Comments

**[user]** on `src/transformers/tokenization_utils_base.py`:

Will this line work for both batched and unbatched cases?

**[user]** on `src/transformers/tokenization_utils_base.py`:

yes, i also added both cases in the new test i added

**[user]** on `src/transformers/tokenization_utils_base.py`:

You're right, sorry!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
