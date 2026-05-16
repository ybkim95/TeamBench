# GH143_mitmproxy_8095: Option to hide quickhelp UI (#5746) — Full Specification (Planner Only)

## Source
- PR: https://github.com/mitmproxy/mitmproxy/pull/8095
- Issue: https://github.com/mitmproxy/mitmproxy/issues/5746
- Repo: https://github.com/mitmproxy/mitmproxy

## Issue Description

#### Problem Description

It would be useful for experienced users to hide quick help bar

#### Proposal
Add option in section "console" like console_help_bar -> true/false

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@mhils):

PRs welcome!

### Comment 2 (@prady0t):

Currently working on this.

### Comment 3 (@prady0t):

Hey @mhils can you help me get started? Where should I look for?

### Comment 4 (@mhils):

The relevant code is in `mitmproxy.tools.console`. This feature is pretty much at the very bottom of my priority list, so I won't look closer into it! Whoever wants this needs to figure it out by themselves.

## PR Review Comments

**@lups2000** on `CHANGELOG.md`:

Allow hiding the Quick Help UI in the mitmproxy console with the 'H' key.

**@lups2000** on `mitmproxy/tools/console/consoleaddons.py`:

Nit: I would rename the command `console_quickhelp_visible` for better clarity

**@lups2000** on `mitmproxy/tools/console/defaultkeys.py`:

```suggestion
    km.add("H", "set console_quickhelp toggle", ["global"], "Toggle quick help bar visibility")
```

**@lups2000** on `mitmproxy/tools/console/statusbar.py`:

```suggestion
        master.options.subscribe(self.sig_options_update, ["console_quickhelp_visible"])
```

**@lups2000** on `mitmproxy/tools/console/statusbar.py`:

```suggestion
        if not self.master.options.console_quickhelp_visible:
```

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `mitmproxy/tools/console/consoleaddons.py` (modified, +6/-0)
- `mitmproxy/tools/console/defaultkeys.py` (modified, +6/-0)
- `mitmproxy/tools/console/statusbar.py` (modified, +19/-0)
- `test/mitmproxy/tools/console/test_statusbar.py` (modified, +91/-0)

## `mitmproxy/tools/console/consoleaddons.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `mitmproxy/tools/console/defaultkeys.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `mitmproxy/tools/console/statusbar.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
