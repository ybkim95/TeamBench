# GH462_pyhf_2639: fix: Use Click v8.x native shell completion — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-hep/pyhf/issues/2622
- Repo: https://github.com/scikit-hep/pyhf

## Issue Description

As https://github.com/click-contrib/click-completion 

> is in maintenance mode only. No new features will be added.

an alternative should be found so that it can be migrated away from. At the moment it is only used in the

https://github.com/scikit-hep/pyhf/blob/35acce8917513d316c8fee83f32239af7d63257c/pyproject.toml#L69

extra, so there is a low impact on pyhf as a project overall.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Also noticed in (withheld: the upstream fix is not part of the task)#issuecomment-3556488160:

> there is a [native `Click` `v8` completion](https://github.com/click-contrib/click-completion/blob/39e8b5453ee2a816b9fd86c563eeecc59060f7af/README.md#L16-L19). c.f. https://click.palletsprojects.com/en/stable/shell-completion/#shell-completion

### Comment 2 ([user]):

[user] I find https://click.palletsprojects.com/en/stable/shell-completion slightly confusing about what specifically would need to happen for `pyhf` to use this. Do you understand and can you give a simple example?

## PR Review Comments

**[user]** on `src/pyhf/cli/complete.py`:

The docstring instructions don't match the actual command output. The docstring shows:
```
echo ". ~/.completions/pyhf-complete.zsh" >> ~/.zshrc
```
But the actual command output includes `-e` flag and `\\n`:
```
echo -e "\\n. ~/.completions/pyhf-complete.zsh" >> ~/.zshrc
```

These should be consistent. Either update the docstring to match the output, or simplify the output to match the docstring.
```suggestion
      echo -e "\\n. ~/.completions/pyhf-complete.sh" >> ~/.bashrc

    \b
    Zsh:
      mkdir -p ~/.completions
      _PYHF_COMPLETE=zsh_source pyhf > ~/.completions/pyhf-complete.zsh
      echo -e "\\n. ~/.completions/pyhf-complete.zsh" >> ~/.zshrc
```

**[user]** on `src/pyhf/cli/complete.py`:

The shell-specific instruction blocks contain duplicated logic and formatting. Consider refactoring to reduce duplication, for example:

```python
instructions = {
    "bash": (
        "mkdir -p ~/.completions\n"
        "_PYHF_COMPLETE=bash_source pyhf > ~/.completions/pyhf-complete.sh\n"
        'echo -e "\\n. ~/.completions/pyhf-complete.sh" >> ~/.bashrc\n'
    ),
    "zsh": (
        "mkdir -p ~/.completions\n"
        "_PYHF_COMPLETE=zsh_source pyhf > ~/.completions/pyhf-complete.zsh\n"
        'echo -e "\\n. ~/.completions/pyhf-complete.zsh" >> ~/.zshrc\n'
    ),
    "fish": "_PYHF_COMPLETE=fish_source pyhf >> ~/.config/fish/completions/pyhf.fish\n",
}

click.echo(click.style(instructions[shell], bold=True))
```

This would make the code more maintainable and reduce the chance of inconsistencies.
```suggestion
    instructions = {
        "bash": (
            "mkdir -p ~/.completions\n"
            "_PYHF_COMPLETE=bash_source pyhf > ~/.completions/pyhf-complete.sh\n"
            'echo -e "\\n. ~/.completions/pyhf-complete.sh" >> ~/.bashrc\n'
        ),
        "zsh": (
            "mkdir -p ~/.completions\n"
            "_PYHF_COMPLETE=zsh_source pyhf > ~/.completions/pyhf-complete.zsh\n"
            'echo -e "\\n. ~/.completions/pyhf-complete.zsh" >> ~/.zshrc\n'
        ),
        "fish": (
            "_PYHF_COMPLETE=fish_source pyhf >> ~/.config/fish/completions/pyhf.fish\n"
        ),
    }
    click.echo(
        click.style(
            instructions[shell],
            bold=True,
        )
    )
```

**[user]** on `src/pyhf/cli/complete.py`:

The docstring instructions don't match the actual command output. The docstring shows:
```
echo ". ~/.completions/pyhf-complete.sh" >> ~/.bashrc
```
But the actual command output includes `-e` flag and `\\n`:
```
echo -e "\\n. ~/.completions/pyhf-complete.sh" >> ~/.bashrc
```

These should be consistent. Either update the docstring to match the output, or simplify the output to match the docstring.

**[user]** on `src/pyhf/cli/complete.py`:

The shell completion instructions are duplicated in both the docstring (lines 20-33) and the `instructions` dictionary (lines 42-55). This creates a maintenance burden where updates must be made in two places. Consider removing the detailed instructions from the docstring and keeping only the high-level description, or generate the help text dynamically from the `instructions` dictionary.
```suggestion
    Supported shells: bash, zsh, fish.

    When run, this command will print instructions for enabling shell completion
    for the specified shell.
```

**[user]** on `src/pyhf/cli/complete.py`:

Missing capitalization at the start of the sentence. The sentence should begin with a capital letter for consistency with standard English grammar.
```suggestion
    click.echo("And then source your shell configuration or restart your shell.")
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
