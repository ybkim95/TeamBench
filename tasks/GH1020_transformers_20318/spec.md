# GH1020_transformers_20318: Fix flakey no_trainer test with seed — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/huggingface/transformers/issues/19733
- Repo: https://github.com/huggingface/transformers

## Issue Description

### System Info

Environment: Circle CI image running `examples_torch`





### Who can help?

[user] 

### Information

- [X] The official example scripts
- [ ] My own modified scripts

### Tasks

- [X] An officially supported task in the `examples` folder (such as GLUE/SQuAD, ...)
- [ ] My own task or dataset (give details below)

### Reproduction

Due to the nature of the issue, unfortunately it cannot be reliably replicated. Examples of this occurring can be found here:

* https://app.circleci.com/pipelines/github/huggingface/transformers/49621/workflows/14c25312-58a5-4b0b-8b41-6c5bec668043/jobs/593213
* https://app.circleci.com/pipelines/gh/huggingface/transformers/49224/workflows/fbae76ab-9259-4695-bb06-475357172587/jobs/589262

### Expected behavior

Occasionally, `test_run_squad_no_trainer` fails on CI runs, even when the PR is not touching code related to the test e.g. I would expect the [output of the tested run](https://github.com/huggingface/transformers/blob/a23819ed6ab852df6d8f04815306440531418260/examples/pytorch/test_accelerate_examples.py#L199), `result`, to be either deterministic or pass reliably when the are otherwise no other changes to the code.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This issue has been automatically marked as stale because it has not had recent activity. If you think this still needs to be addressed please comment on this thread.

Please note that issues that do not follow the [contributing guidelines](https://github.com/huggingface/transformers/blob/main/CONTRIBUTING.md) are likely to be ignored.

### Comment 2 ([user]):

ping [user] ;-)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
