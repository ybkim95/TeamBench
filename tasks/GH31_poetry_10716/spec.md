# GH31_poetry_10716: fix(env): support posix-compliant shells in `env activate` on Windows — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/python-poetry/poetry/issues/10395
- Repo: https://github.com/python-poetry/poetry

## Issue Description

### Description

The `eval $(poetry env activate)` command does not work in Windows when running it in a Bash shell (or similar), because it does not output `.` or `source` at the beginning. Instead the command outputs only the single-quoted path to the activate script, which is meant to be used as argument to Powershell's `Invoke-Expression` command.

The `poetry env activate` command should behave the same way, regardless of the operating system, especially for any shells other than Powershell and cmd.

The reason is because of [an `if WINDOWS:` line](https://github.com/python-poetry/poetry/blame/84eeadc21f92a04d46ea769e3e39d7c902e44136/src/poetry/console/commands/env/activate.py#L58) in `poetry.console.commands.env.activate` module, which actually only works for Powershell (but nothing can be done for cmd). One simple way to fix this would be to set `command` to `""` for the `["powershell", "pwsh"]` and `"cmd"` cases and test `if not command:` instead of testing if it's Windows or not.

### Workarounds

A workaround is to add a `.` (or `source`) after `eval`: `eval . $(poetry env activate)`

### Poetry Installation Method

pipx

### Operating System

Windows

### Poetry Version

2.1.3

### Poetry Configuration

```bash session
Not relevant
```

### Python Sysconfig

<details>
  <summary>sysconfig.log</summary>
  <!-- Please leave one blank line below for enabling the code block rendering. -->

  ```
Not relevant
  ```
</details>

### Example pyproject.toml

```TOML

```

### Poetry Runtime Logs

<details>
  <summary>poetry-runtime.log</summary>
  <!-- Please leave one blank line below for enabling the code block rendering. -->

  ```
Not relevant
  ```
</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

PRs are welcome.

### Comment 2 ([user]):

[user] Has this issue been solved? If not, may I give it a try?

### Comment 3 ([user]):

Hi, I’d like to work on this issue as my first contribution.

### Comment 4 ([user]):

Go ahead. There is already #10415. However, the author has not reacted to my feedback for some while, so they may have lost interest.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
