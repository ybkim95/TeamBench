# GH977_transformers_34889: Fix test_eager_matches_sdpa_inference for XPU backend — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/transformers

## PR Description

Included fixes:
* Use `torch.nn.attention.sdpa_kernel` instead of deprecated `torch.backends.cuda.sdp_kernel`
* Use `torch.amp.autocast` instead of deprecated `torch.cuda.amp.autocast` in nemotron
* Reuse CUDA MATH thresholds in for XPU (as of PyTorch 2.5 XPU backend supports only `torch.nn.attention.SDPBackend.MATH`)

Fixes: #34888
CC: [user] [user]

## PR Review Comments

**[user]** on `tests/models/musicgen/test_modeling_musicgen.py`:

why `enable_kernels` not set to False here?

**[user]** on `tests/models/musicgen_melody/test_modeling_musicgen_melody.py`:

the same here.

**[user]** on `tests/models/musicgen/test_modeling_musicgen.py`:

I missed it. Fixed.

**[user]** on `tests/models/musicgen_melody/test_modeling_musicgen_melody.py`:

fixed

**[user]** on `tests/models/mimi/test_modeling_mimi.py`:

nit:

although xpu only support MATH, does it means the results from XPU will be the same as, say CUDA? Otherwise, I don't see the reason to reuse CUDA threshold.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
