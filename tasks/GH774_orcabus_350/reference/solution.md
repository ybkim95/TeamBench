# Reference solution — GH774_orcabus_350

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH774_orcabus_350`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH774_orcabus_350/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `config/constants.ts` (modified, +4/-4)
- `lib/workload/components/event-workflowrunstatechange-internal-to-inputmaker-sfn/lambdas/generate_workflow_run_name_py/generate_workflow_run_name.py` (modified, +2/-2)
- `lib/workload/stateless/stacks/bclconvert-interop-qc-pipeline-manager/scripts/trigger_bclconvert_interop_qc.sh` (modified, +8/-8)
- `lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/lambdas/query_bclconvert_outputs_handler_py/query_bclconvert_outputs_handler.py` (modified, +19/-19)

## `lib/workload/components/event-workflowrunstatechange-internal-to-inputmaker-sfn/lambdas/generate_workflow_run_name_py/generate_workflow_run_name.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/lambdas/query_bclconvert_outputs_handler_py/query_bclconvert_outputs_handler.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `lib/workload/components/event-workflowrunstatechange-internal-to-inputmaker-sfn/lambdas/generate_workflow_run_name_py/generate_workflow_run_name.py`
- `lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/lambdas/query_bclconvert_outputs_handler_py/query_bclconvert_outputs_handler.py`
