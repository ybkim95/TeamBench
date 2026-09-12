# GH1145_wandb_11237: fix: ignore ipython magic registration errors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Description
-----------
Fixes WB-30691.

Certain notebook environments appear to leave IPython's global "pending magics" registry in a polluted state (e.g. containing an `install_from_stage` entry). When `wandb` auto-registers its magics on import, `@magics_class` can accidentally pick up these foreign entries, causing `ipython.register_magics(WandBMagics)` to fail with `AttributeError` for missing methods (e.g. `install_from_stage_line_magic`) and breaking `import wandb`.

With this PR, we'll simply ignore such errors not to break `import wandb`. The `wandb` magic won't be available, but it feels like this issue should be addressed on the custom ipython side. If absolutely necessary, we can follow-up with some hacky worksarounds.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
