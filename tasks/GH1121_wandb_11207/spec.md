# GH1121_wandb_11207: fix: report and ignore invalid settings files — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Fixes WB-30392.

Makes `Settings.update_from_system_settings()`, which runs whenever the global settings object is initialized, report and skip settings files with invalid settings values.

This fixes a regression in 0.24.0 where after `wandb login --host invalid-host` it was necessary to fix the settings file manually. Now, `wandb login --cloud` or the like will succeed (but print an error message that is perhaps redundant).

```
❯ wandb login --cloud
wandb: Loading settings from /Users/timoffex/.config/wandb/settings
wandb: ERROR 1 validation error for Settings
wandb: ERROR base_url
wandb: ERROR   Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='invalid-host', input_type=str]
wandb: ERROR     For further information visit https://errors.pydantic.dev/2.12/v/url_parsing
wandb: Updated settings file /Users/timoffex/.config/wandb/settings
wandb: [wandb.login()] Loaded credentials for https://api.wandb.ai from /Users/timoffex/.netrc.
wandb: Currently logged in as: timoffex (wandb) to https://api.wandb.ai. Use `wandb login --relogin` to force relogin
```

A small wrinkle in the exception handling code is that some of our field validators raise `UsageError` instead of `ValueError`. Pydantic understands ValueErrors and wraps them in `ValidationError`, which has enough detail for us to print without a traceback. But with other error types, we cannot distinguish validation errors from programming bugs, so we must print a traceback.

Example of what happens when a `project` field contains slashes:

```
❯ wandb login --cloud         
wandb: Loading settings from /Users/timoffex/.config/wandb/settings
wandb: ERROR Traceback (most recent call last):
wandb: ERROR   File "/Users/timoffex/Documents/workspace/wandb/wandb/sdk/wandb_settings.py", line 1828, in update_from_system_settings
wandb: ERROR     parsed_settings = _parse_system_settings(system_settings)
wandb: ERROR   File "/Users/timoffex/Documents/workspace/wandb/wandb/sdk/wandb_settings.py", line 2289, in _parse_system_settings
wandb: ERROR     return Settings(**fields)
wandb: ERROR   File "/Users/timoffex/Documents/workspace/testing/.venv/lib/python3.10/site-packages/pydantic/main.py", line 250, in __init__
wandb: ERROR     validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
wandb: ERROR   File "/Users/timoffex/Documents/workspace/wandb/wandb/sdk/wandb_settings.py", line 1212, in validate_project
wandb: ERROR     raise UsageError(
wandb: ERROR wandb.errors.errors.UsageError: Invalid project name 'slashes/not/allowed': cannot contain characters '/,\\,#,?,%,:', found '/'
wandb: ERROR 
wandb: [wandb.login()] Loaded credentials for https://api.wandb.ai from /Users/timoffex/.netrc.
wandb: Currently logged in as: timoffex (wandb) to https://api.wandb.ai. Use `wandb login --relogin` to force relogin
```

## PR Review Comments

**[user]** on `wandb/sdk/wandb_settings.py`:

will? :)

**[user]** on `wandb/sdk/wandb_settings.py`:

i know it's unrelated

**[user]** on `wandb/sdk/wandb_settings.py`:

from BREAKING.md:

\> Can do after May 2026. It depends on when the PyTorch Lightning W&B integration (and possibly others) can be updated to not pass `anonymous` (even set to `None`)

I haven't checked in with PTL, we might need to send a PR

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
