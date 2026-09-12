# GH1046_transformers_43675: make sure hub errors are surfaced — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/transformers

## PR Description

# What does this PR do?

in `PreTrainedTokenizerBase.from_pretrained` this commit (withheld: the upstream fix is not part of the task)#diff-85b29486a884f445b1014[…]f4ae701ee758a754fddcc1L1679 silenced hub errors, this is surfaced by 

```
pytest -sv tests/models/auto/test_tokenization_auto.py::AutoTokenizerTest::test_tokenizer_identifier_non_existent
```

with 

```
E           AssertionError: "julien-c/herlolip-not-exists is not a local folder and is not a valid model identifier" does not match "401 Client Error. (Request ID: Root=1-69806dfe-29b61b47408bd03420a3cdac;e2386594-f169-4d1b-9171-050ec211b4c8)
```

This patch removes the try/except block

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
