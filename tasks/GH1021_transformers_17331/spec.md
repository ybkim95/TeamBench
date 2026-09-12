# GH1021_transformers_17331: Fix metric calculation in examples and setup tests to run on multi-gpu for no_trainer scripts — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/huggingface/transformers/issues/17214
- Repo: https://github.com/huggingface/transformers

## Issue Description

### System Info

```shell
When I finetuned the text classification model based on the glue no trainer script, I found a bug in our script.
The URL is below:
https://github.com/huggingface/transformers/blob/main/examples/pytorch/text-classification/run_glue_no_trainer.py#L525

When we use the accelerator for multi-GPU training, the code should transfer from 
if step == len(eval_dataloader)
to 
if step == len(eval_dataloader) -1
Otherwise, it cannot work to filter the last step duplicated samples.
```


### Who can help?

_No response_

### Information

- [ ] The official example scripts
- [x] My own modified scripts

### Tasks

- [ ] An officially supported task in the `examples` folder (such as GLUE/SQuAD, ...)
- [x] My own task or dataset (give details below)

### Reproduction

just run the script with a text classification using multi-GPU accelerator. The problem occurs in the last step for duplicated samples.

### Expected behavior

```shell
I think it should be fixed soon.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
