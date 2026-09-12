# GH1191_pytorch_172105: A few weights_only unpickler fixes — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytorch/pytorch

## PR Description

Fixes the following 
- Adds type validation to `SETITEM`/`SETITEMS`, to prevent tensor updates during `torch.load`
- Only print `type(pid[0])` rather than `pid[0]` in error message for `BINPERSID`
- Validate `numel` in .pkl for storage matches size of storage saved to zipfile in `get_storage_from_record`


Stack from [ghstack](https://github.com/ezyang/ghstack) (oldest at bottom):
* __->__ #170085



cc [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
