# GH774_orcabus_350: Use hyphens over underscores when generating icav2 paths — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/umccr/orcabus/issues/349
- Repo: https://github.com/umccr/orcabus

## PR Description

Resolves #349 

Also Fixed shell script to point to development, instead of trial project in some examples

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

See [Slack thread](https://umccr.slack.com/archives/C025TLC7D/p1718269513888569?thread_ts=1717638564.248829&cid=C025TLC7D) for change request background

## PR Review Comments

**[user]** on `config/constants.ts`:

Just confirming; do we want to remove `-data` suffix from the mid path too?

No strong preference from me. If we decided so, I will update [the design doc](https://umccr.slack.com/archives/C025TLC7D/p1718269513888569?thread_ts=1717638564.248829&cid=C025TLC7D) accordingly.

[user] [user] 

This must be the last bit that I might have missed yesterday discussion, Sorry. Let us finalise here, folks.

**[user]** on `lib/workload/stateless/stacks/bclconvert-interop-qc-pipeline-manager/scripts/trigger_bclconvert_interop_qc.sh`:

Perhaps, these mid paths might have to change accordingly too, Alexis? 
Lines 24, 25, 35, 36.

**[user]** on `lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/lambdas/query_bclconvert_outputs_handler_py/query_bclconvert_outputs_handler.py`:

Same, mid path.

**[user]** on `config/constants.ts`:

No strong feelings either, but I'd personally would keep the "-data". 
It's more specifically talking about "data" and is less easily confused. For example AWS has primary (and secondary) analysis workflows, the outputs of which would NOT fall under our "primary" definition.

**[user]** on `config/constants.ts`:

Not fussed either. Compare:

- `analysis-data`
- `analysis-cache`
- `primary-data`

vs.

- `analysis`
- `analysis-cache`
- `primary`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
