# GH1089_pytorch_lightni_8421: Hash values in LightningEnum instead of name. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## PR Description

## What does this PR do?

Fixes enums hash by name and not by value. For example:

```
TrainerFn.FITTING in (None, "fit") # True
TrainerFn.FITTING in {None, "fit"} # False
```

Both should have the same result.

## Before submitting
- [ ] Was this discussed/approved via a GitHub issue? (not for typos and docs)
- [x] Did you read the [contributor guideline](https://github.com/PyTorchLightning/pytorch-lightning/blob/master/.github/CONTRIBUTING.md), **Pull Request** section?
- [x] Did you make sure your PR does only one thing, instead of bundling different changes together?
- [x] Did you make sure to update the documentation with your changes? (if necessary)
- [x] Did you write any new necessary tests? (not for typos and docs)
- [x] Did you verify new and existing tests pass locally with your changes?
- [ ] Did you update the [CHANGELOG](https://github.com/PyTorchLightning/pytorch-lightning/blob/master/CHANGELOG.md)? (not for typos, docs, test updates, or internal minor changes/refactorings)
- [ ] Did you list all the breaking changes introduced by this pull request?

## PR review
Anyone in the community is free to review the PR once the tests have passed.
Before you start reviewing make sure you have read [Review guidelines](https://github.com/PyTorchLightning/pytorch-lightning/wiki/Review-guidelines). In short, see the following bullet-list:

 - [x] Is this pull request ready for review? (if not, please submit in draft mode)
 - [ ] Check that all items from **Before submitting** are resolved
 - [x] Make sure the title is self-explanatory and the description concisely explains the PR
 - [x] Add labels and milestones (and optionally projects) to the PR so it can be classified

## Did you have fun?
Make sure you had fun coding 🙃

## PR Review Comments

**[user]** on `pytorch_lightning/utilities/enums.py`:

Need this so it is also case invariant for hash. So this works just as `__eq__`

```suggestion
        return hash(self.value.lower())
```

**[user]** on `pytorch_lightning/utilities/enums.py`:

what is the diff to the above?
```suggestion
```

**[user]** on `pytorch_lightning/utilities/enums.py`:

[user] It is the test for the change in this PR. You can see it would fail in master

So can you revert the commit?

**[user]** on `pytorch_lightning/utilities/enums.py`:

ok, but in such case rather have this in test as it does not give any extra value in examples

**[user]** on `tests/utilities/test_enums.py`:

you have different test cases in the PR description. 
double check?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
