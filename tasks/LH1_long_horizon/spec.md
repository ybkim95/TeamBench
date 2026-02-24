# LH1: Long-Horizon Workflow with Failure Injection

## Goal
Execute a 15-step data processing pipeline. Two steps will fail on first attempt
and must be retried/recovered.

## Hard Requirements

1. Run `python workflow.py` which executes steps 1-15 sequentially.
2. The workflow reads `pipeline_config.json` for step definitions.
3. **Step 5** will fail on first attempt (transient error, creates `step5_fail` marker).
   - Fix: delete the marker file `intermediates/step5_fail` and re-run step 5.
4. **Step 11** will fail on first attempt (transient error, creates `step11_fail` marker).
   - Fix: delete the marker file `intermediates/step11_fail`, regenerate from step 10 output, and re-run step 11.
5. Final output: `output/final_result.json` must contain:
   - `{"steps_completed": 15, "recovered_failures": 2, "checksum": "<sha256>"}`
6. The `checksum` is SHA-256 of concatenated step outputs.
7. A `output/workflow_log.jsonl` must record every step execution (pass/fail/retry).
8. Total step executions must be <= 19 (15 normal + 2 failures + 2 retries).

## Deliverables
- Fixed workflow producing correct `final_result.json` and `workflow_log.jsonl`.
- Verifier must confirm step count, recovery, and checksum.
