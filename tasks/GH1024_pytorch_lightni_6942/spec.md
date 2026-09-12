# GH1024_pytorch_lightni_6942: [fix] Add a cluster environment teardown to clean up environment state — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## PR Description

## What does this PR do?

<!--
Please include a summary of the change and which issue is fixed.
 Please also include relevant motivation and context.
 List any dependencies that are required for this change.

If we didn't discuss your PR in Github issues there's a high chance it will not be merged.

The following links the related issue to the PR (https://docs.github.com/en/free-pro-team@latest/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword)
-->
Discussion in #6853 
Fixes part of #6303

https://github.com/PyTorchLightning/pytorch-lightning/blob/f852a4f5925211d6bb9dac231b9185e3e6814b13/pytorch_lightning/plugins/training_type/ddp.py#L283-L285

This is a bug for users who have subsequent calls to 
```
trainer.fit(...)
trainer.test(...)
```
and who launched with torchelastic. The world size environment variable is mistakenly removed, causing the trainer.test call to fail. As a result, we introduce a `teardown` hook on the cluster environment to resolve this issue. the teardown for torchelastic and slurm are no-ops, but for the lightning environment, we can remove the world size after the sub-process calls finish.

## Before submitting
- [x] Was this discussed/approved via a GitHub issue? (not for typos and docs)
- [x] Did you read the [contributor guideline](https://github.com/PyTorchLightning/pytorch-lightning/blob/master/.github/CONTRIBUTING.md), **Pull Request** section?
- [x] Did you make sure your PR does only one thing, instead of bundling different changes together?
- [x] Did you make sure to update the documentation with your changes? (if necessary)
- [ ] Did you write any new necessary tests? (not for typos and docs)
- [x] Did you verify new and existing tests pass locally with your changes?
- [x] Did you update the [CHANGELOG](https://github.com/PyTorchLightning/pytorch-lightning/blob/master/CHANGELOG.md)? (not for typos, docs, test updates, or internal minor changes/refactorings)

<!-- For CHANGELOG separate each item in the unreleased section by a blank line to reduce collisions -->

## PR review
Anyone in the community is free to review the PR once the tests have passed.
Before you start reviewing make sure you have read [Review guidelines](https://github.com/PyTorchLightning/pytorch-lightning/wiki/Review-guidelines). In short, see the following bullet-list:

 - [x] Is this pull request ready for review? (if not, please submit in draft mode)
 - [x] Check that all items from **Before submitting** are resolved
 - [x] Make sure the title is self-explanatory and the description concisely explains the PR
 - [x] Add labels and milestones (and optionally projects) to the PR so it can be classified

## Did you have fun?
Make sure you had fun coding 🙃

## PR Review Comments

**[user]** on `pytorch_lightning/plugins/training_type/ddp.py`:

how about we ask the cluster env to clean up?

self.cluster_environment.clean_up / teardown

**[user]** on `pytorch_lightning/plugins/training_type/ddp.py`:

yes totally agreed. i also don't know why this is being called in post_dispatch instead of the plugin's teardown

**[user]** on `CHANGELOG.md`:

```suggestion


- Added a `teardown` hook to `ClusterEnvironment` ([#6942]((withheld: the upstream fix is not part of the task)))
```

**[user]** on `CHANGELOG.md`:

```suggestion


- Fixed incorrect removal of `WORLD_SIZE` environment variable in DDP training when launching with torch distributed/torchelastic ([#6942]((withheld: the upstream fix is not part of the task)))
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
