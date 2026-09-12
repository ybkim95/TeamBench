# GH1069_transformers_29370: 🚨 Fully revert atomic checkpointing 🚨 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/transformers

## PR Description

# What does this PR do?

As discussed offline, while on paper having atomic checkpointing was a good idea, it's unmaintainable by the core maintainers and has resulted in an influx of issues from users considering the wide variety of storage options available to them. (and untestable)

As the feature request, while reasonable and from a good mindset, was not due to an outright bug, we are reverting it entirely. 

Related PRs:

(withheld: the upstream fix is not part of the task), (withheld: the upstream fix is not part of the task)

Did revert based on this commit: (withheld: the upstream fix is not part of the task)

Related issues: 
* https://github.com/huggingface/transformers/issues/27925
* https://github.com/huggingface/transformers/issues/28027
* https://github.com/huggingface/transformers/issues/29382


## Before submitting
- [ ] This PR fixes a typo or improves the docs (you can dismiss the other checks if that's the case).
- [x] Did you read the [contributor guideline](https://github.com/huggingface/transformers/blob/main/CONTRIBUTING.md#create-a-pull-request),
      Pull Request section?
- [ ] Was this discussed/approved via a Github issue or the [forum](https://discuss.huggingface.co/)? Please add a link
      to it if that's the case.
- [ ] Did you make sure to update the documentation with your changes? Here are the
      [documentation guidelines](https://github.com/huggingface/transformers/tree/main/docs), and
      [here are tips on formatting docstrings](https://github.com/huggingface/transformers/tree/main/docs#writing-source-documentation).
- [ ] Did you write any new necessary tests?


## Who can review?

Anyone in the community is free to review the PR once the tests have passed. Feel free to tag
members/contributors who may be interested in your PR.

[user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
