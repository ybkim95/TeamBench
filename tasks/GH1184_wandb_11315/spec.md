# GH1184_wandb_11315: fix(launch): fallback to sh when bash is unavailable in local container runner — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Description
-----------
- Fixes https://wandb.atlassian.net/browse/WB-31183

This PR fixes a launch-agent regression where sweep launch jobs fail to start in environments that do not have `bash` installed (e.g. Chainguard-based images).  
`LocalContainerRunner` no longer hardcodes `bash -c`; it now resolves a compatible shell at runtime (`bash` first, then `sh` on POSIX, `cmd /C` on Windows) and raises a clear `LaunchError` if no shell is available.

Tests were updated to validate both implementation behavior and interface-level behavior:
- Existing local-container runner assertions now accept `bash` or `sh` on POSIX.
- Added interface-level tests through `LocalContainerRunner.run()` for:
  - fallback to `sh` when `bash` is missing
  - clear failure when neither `bash` nor `sh` is present
- Added focused shell-resolution tests for `bash` preference, `sh` fallback, and no-shell error.

<!--
NEW: We're using a new changelog format that's more useful for users. Please
see CHANGELOG.unreleased.md for details and update on relevant changes such as feature
additions, bug fixes, or removals/deprecations.
-->
- [X] I updated CHANGELOG.unreleased.md, or it's not applicable


Testing
-------
How was this PR tested?

Ran targeted unit tests with the project SDK Python environment:

```
pytest -q tests/unit_tests/test_launch/test_runner/test_local_container.py
````

Result:
- 7 passed, 1 warning (`PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope`, pre-existing)

Validated behavior in the official `wandb/launch-agent:0.21.0` image (where `bash` is not installed), using the same `_run_entry_point` path that failed in customer logs.

- Baseline (`wandb/launch-agent:0.21.0`, stock code):
  - `which bash` -> `bash not found`
  - `_run_entry_point("echo shell_fallback_ok")` raised `FileNotFoundError: 'bash'`
  - Result: `ok: False`, `logs: ''`

- Patched code (same `0.21.0` image, local branch mounted via `PYTHONPATH=/src`):
  - `_run_entry_point("echo shell_fallback_ok")` succeeded
  - Result: `ok: True`, `logs: 'shell_fallback_ok'`

This confirms the fix resolves the startup failure by using shell fallback behavior when `bash` is unavailable.
<!--
Ensure PR title compliance with the [conventional commits standards](https://github.com/wandb/wandb/blob/main/CONTRIBUTING.md#conventional-commits)
-->

## PR Review Comments

**[user]** on `tests/unit_tests/test_launch/test_runner/test_local_container.py`:

```suggestion
    command = mock_popen.call_args[0][0]
    assert len(command) == 3, "Expected [shell, '-c', command]"
    assert os.path.basename(command[0]) == "sh"
    assert command[1] == "-c"
    assert "echo hello world" in command[2]
```

Just ensuring that the command we've specified in `mock_launch_project` is actually carried through

**[user]** on `tests/unit_tests/test_launch/test_runner/test_local_container.py`:

Could we add a windows version of this test?

**[user]** on `tests/unit_tests/test_launch/test_runner/test_local_container.py`:

added!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
