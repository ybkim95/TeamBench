# GH1203_wandb_11226: fix(sweeps): stop the sweep when the sweep cannot be found — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Description
-----------
Fixes https://wandb.atlassian.net/browse/WB-27983

When a sweep is deleted while an agent is running, the agent would continuously receive 404 errors from the server and keep running indefinitely, spamming the logs with:
`wandb: ERROR Error while calling W&B API: agent not found (<Response [404]>)` This results in inefficient compute usage for the customer.

This PR adds better handling for this scenario. When `agent_heartbeat()` receives a 404 response, it now raises a `SweepNotFoundError` exception. All agent entry points catch this exception and exit cleanly with the error message: 
`wandb: ERROR Sweep was deleted or agent was not found. Stopping sweep.`


<!--
NEW: We're using a new changelog format that's more useful for users. Please
see CHANGELOG.unreleased.md for details and update on relevant changes such as feature
additions, bug fixes, or removals/deprecations.
-->
- [x] I updated CHANGELOG.unreleased.md, or it's not applicable


Testing
-------
How was this PR tested?

Added unit and system tests to verify the new exception is raised and handled by exiting the agent.

Manual testing via SDK and CLI to confirm exiting behavior:

SDK logs
```bash
$ python test_sweep_deletion.py 
wandb: [wandb.login()] Loaded credentials for https://api.wandb.ai from ~/.netrc.
Create sweep with ID: abc123xy
Sweep URL: https://wandb.ai/my-team/my-project/sweeps/abc123xy
wandb: Agent Starting Run: run123id with config:
wandb:  x: 0.03987346120382068
wandb:  y: 7
wandb: Currently logged in as: user (my-team) to https://api.wandb.ai. Use `wandb login --relogin` to force relogin
wandb: Tracking run with wandb version 0.24.1.dev1
wandb: Run data is saved locally in ./wandb/run-20260123_100542-run123id
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run celestial-sweep-1
wandb: ⭐️ View project at https://wandb.ai/my-team/my-project
wandb: 🧹 View sweep at https://wandb.ai/my-team/my-project/sweeps/abc123xy
wandb: 🚀 View run at https://wandb.ai/my-team/my-project/runs/run123id
wandb: ERROR Error while calling W&B API: agent not found (<Response [404]>)
wandb: ERROR Sweep was deleted or agent was not found. Stopping sweep.
```

CLI logs
```bash
$ wandb sweep --entity my-team --project my-project sweep.yaml
wandb: Creating sweep from: sweep.yaml
wandb: Creating sweep with ID: abc123xy
wandb: View sweep at: https://wandb.ai/my-team/my-project/sweeps/abc123xy
wandb: Run sweep agent with: wandb agent my-team/my-project/abc123xy

$ wandb agent my-team/my-project/abc123xy
wandb: Starting wandb agent 🕵️
wandb: [wandb.login()] Loaded credentials for https://api.wandb.ai from ~/.netrc.
2026-01-22 16:52:55,187 - wandb.wandb_agent - INFO - Running runs: []
2026-01-22 16:52:55,645 - wandb.wandb_agent - INFO - Agent received command: run
2026-01-22 16:52:55,645 - wandb.wandb_agent - INFO - Agent starting run with config:
        x: 0.040946041354035546
        y: 3
2026-01-22 16:52:55,646 - wandb.wandb_agent - INFO - About to run command: /usr/bin/env python train.py --x=0.040946041354035546 --y=3
wandb: Currently logged in as: user (my-team) to https://api.wandb.ai. Use `wandb login --relogin` to force relogin
wandb: Tracking run with wandb version 0.24.1.dev1
wandb: Run data is saved locally in ./wandb/run-20260122_165256-run123id
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run brisk-sweep-1
wandb: ⭐️ View project at https://wandb.ai/my-team/my-project
wandb: 🧹 View sweep at https://wandb.ai/my-team/my-project/sweeps/abc123xy
wandb: 🚀 View run at https://wandb.ai/my-team/my-project/runs/run123id
2026-01-22 16:53:00,651 - wandb.wandb_agent - INFO - Running runs: ['run123id']
wandb: ERROR Error while calling W&B API: agent not found (<Response [404]>)
wandb: ERROR Sweep was deleted or agent was not found. Stopping sweep.
wandb: Terminating and syncing runs. Press ctrl-c to kill.
```

<!--
Ensure PR title compliance with the [conventional commits standards](https://github.com/wandb/wandb/blob/main/CONTRIBUTING.md#conventional-commits)
-->

## PR Review Comments

**[user]** on `wandb/sdk/internal/internal_api.py`:

Why do we only raise an error on 404? Why not other client and server error codes?

**[user]** on `wandb/wandb_agent.py`:

Can you confirm whether the CLI command itself returns a non-zero exit code in this case? If not, can you make it do that?

**[user]** on `tests/system_tests/test_sweep/test_wandb_agent_full.py`:

Do we have integration tests for the CLI? If not, not a blocker, but it's something we should consider adding...

**[user]** on `wandb/wandb_agent.py`:

Looked into it and I believe the CLI will return a 0 exit code, so I changed the exit code handling a bit so the CLI can explicitly handle sweeps related exceptions and exit with the proper code. PTAL at this commit: (withheld: the upstream fix is not part of the task)commits/e76998b04c7306643f5b41c3fade7ecb403f82b3

I added todos so we can do the same when max failures is reached and when flapping occurs.

**[user]** on `tests/system_tests/test_sweep/test_wandb_agent_full.py`:

Agreed, I think we have one partial integration test that uses the CLI.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
