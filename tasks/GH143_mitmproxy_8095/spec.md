# GH143_mitmproxy_8095: Option to hide quickhelp UI (#5746) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/mitmproxy/mitmproxy/issues/5746
- Repo: https://github.com/mitmproxy/mitmproxy

## Issue Description

#### Problem Description

It would be useful for experienced users to hide quick help bar

#### Proposal
Add option in section "console" like console_help_bar -> true/false

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

PRs welcome!

### Comment 2 ([user]):

Currently working on this.

### Comment 3 ([user]):

Hey [user] can you help me get started? Where should I look for?

### Comment 4 ([user]):

The relevant code is in `mitmproxy.tools.console`. This feature is pretty much at the very bottom of my priority list, so I won't look closer into it! Whoever wants this needs to figure it out by themselves.

## PR Review Comments

**[user]** on `CHANGELOG.md`:

Allow hiding the Quick Help UI in the mitmproxy console with the 'H' key.

**[user]** on `mitmproxy/tools/console/consoleaddons.py`:

Nit: I would rename the command `console_quickhelp_visible` for better clarity

**[user]** on `mitmproxy/tools/console/defaultkeys.py`:

```suggestion
    km.add("H", "set console_quickhelp toggle", ["global"], "Toggle quick help bar visibility")
```

**[user]** on `mitmproxy/tools/console/statusbar.py`:

```suggestion
        master.options.subscribe(self.sig_options_update, ["console_quickhelp_visible"])
```

**[user]** on `mitmproxy/tools/console/statusbar.py`:

```suggestion
        if not self.master.options.console_quickhelp_visible:
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
