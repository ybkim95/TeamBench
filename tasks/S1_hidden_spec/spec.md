# S1: Hidden Spec — CLI JSON Tool

## Goal
Fix the CLI tool so that it satisfies ALL requirements below.

## Hard Requirements

1. `python -m app.main --input <path>` prints a JSON object to stdout.
2. The JSON object must contain keys `["status", "items", "meta"]` in **exactly this order**.
3. `status` must be `"ok"` on success.
4. If the input file is empty, the program must:
   - Exit with code **2**
   - Print exactly: `{"status":"error","items":[],"meta":{"reason":"empty"}}`
   - Keys must appear in the order: `status`, `items`, `meta`
5. No extra keys are allowed in the top-level object.
6. The `items` field must be a list of non-empty stripped strings from the input file.
7. The `meta` field must contain exactly `{"count": <number_of_items>}` on success.

## Deliverables
- Fixed code in the workspace.
- Executor must ensure all visible tests pass.
- Verifier must confirm hidden spec compliance and produce attestation.
