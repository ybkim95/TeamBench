# P1: Policy-Driven Config Change

## Goal
Generate a configuration file (`output/config.json`) that complies with ALL rules
defined below.

## Hard Requirements

1. Produce `output/config.json` that satisfies every rule below.
2. The config must be valid JSON with exact key names as specified.
3. Policy rules:
   - `max_connections`: must be between 100 and 500 inclusive
   - `timeout_sec`: must be exactly 30
   - `ssl_enabled`: must be true
   - `log_level`: must be one of ["warn", "error"] (not "info" or "debug")
   - `retry_count`: must be 3
   - `cors_origins`: must be an empty list `[]` (no wildcard)
   - `rate_limit_rpm`: must be between 60 and 120 inclusive
   - `auth_method`: must be "jwt" (not "basic" or "none")
4. No extra keys are allowed beyond those 8.
5. The initial `config.json` template in the workspace has intentional policy violations.

## Policy Source (for Planner reference)

The policy document (`corpus/policy.txt`) contains:
- Rule 1: max_connections must be between 100 and 500 (inclusive)
- Rule 2: timeout_sec must be exactly 30 seconds
- Rule 3: ssl_enabled must be true
- Rule 4: log_level must be "warn" or "error"
- Rule 5: retry_count must be exactly 3
- Rule 6: cors_origins must be an empty list []
- Rule 7: rate_limit_rpm must be between 60 and 120 (inclusive)
- Rule 8: auth_method must be "jwt"
- No additional configuration keys are permitted beyond the 8 listed above.

## Deliverables
- Corrected `output/config.json` in workspace.
- Verifier must check each policy rule and produce attestation.
