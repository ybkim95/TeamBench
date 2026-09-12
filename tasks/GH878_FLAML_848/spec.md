# GH878_FLAML_848: fix bug related to _choice_ — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1234
- Repo: https://github.com/microsoft/FLAML

## Issue Description

I got this error in notebook/autogen_agentchat_groupchat_research.ipynb
error: 
Rate limit reached for default-gpt-4 in organization org-dRcLOmvP4zyFH42QuipEteyV on tokens per min. Limit: 40000 / min. Please try again in 1ms. Contact us through our help center at help.openai.com if you continue to have issues.


got it too, in notebook/agentchat_teaching.ipynb

error : 
InvalidRequestError: This model's maximum context length is 8192 tokens. However, your messages resulted in 9297 tokens. Please reduce the length of the messages.


Please modify the code so that it works even if it is only used as an OPENAI API, or provide a guide to apply for an AZURE API KEY.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
