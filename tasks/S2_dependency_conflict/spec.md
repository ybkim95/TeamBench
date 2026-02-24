# S2: Dependency Conflict Trap

## Goal
Fix the Python project so that `make test` passes.

## Hard Requirements

1. The project has a `Makefile` with a `test` target that runs `python -m pytest tests/ -q`.
2. The project depends on two libraries (provided as local packages in `vendor/`):
   - `libfoo==1.2.0` requires `utils>=2.0,<3.0`
   - `libbar==0.9.1` requires `utils>=1.0,<2.0`
3. The **correct resolution** is:
   - Pin `utils==2.0.0` (satisfies libfoo)
   - Patch `libbar/core.py` to be compatible with utils 2.x (one-line fix: `from utils.v2 import helper` instead of `from utils.legacy import helper`)
4. Simply downgrading utils to 1.x will break libfoo (test catches this).
5. `requirements.txt` must list exact pinned versions.
6. No additional packages may be introduced.
7. All 4 test cases in `tests/test_integration.py` must pass.

## Deliverables
- Fixed code + `requirements.txt` in workspace.
- Verifier must confirm all constraints and produce attestation.
