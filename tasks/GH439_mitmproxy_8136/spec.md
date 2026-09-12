# GH439_mitmproxy_8136: cleanup: removed unused functions/classes and scripts — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mitmproxy/mitmproxy

## PR Description

Hihi, was using this over the weekend, got a lil bit bored and did some cleanups.. 

Removed these things: 

- `setbit()`/`getbit()` in `mitmproxy/utils/bits.py`: entire file deleted, zero callers
- `SearchError` in `mitmproxy/tools/console/flowview.py`: exception never raised
- `colorize_url()` in `mitmproxy/tools/console/common.py`: zero callers
- `fcol()` in `mitmproxy/tools/console/options.py`: zero callers (diff from the used `fcol` in `common.py`)
- `view_orders` in `mitmproxy/tools/console/consoleaddons.py`: no references

Also a question: `save_settings()` in `tools/web/static_viewer.py` was added in a while back but never wired into `export()`. Not quite sure if this was intentional or should it be called there? Reverted it it in second commit, so not doing anything to that for now. 

Found with [Skylos](https://github.com/duriantaco/skylos), a dead code detection tool.

- [ ] I have updated tests where applicable.                                                        
- [ ] I have added an entry to the CHANGELOG. 

Not sure if these 2 are required for code cleanup. I did a grep for the checks.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
