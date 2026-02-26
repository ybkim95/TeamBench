# O3: Log Analysis + Root Cause Fix

## Goal

Identify the root cause of intermittent production failures in `user-service` by
analysing structured logs, then apply the minimal correct fix so the service
operates without errors.

## Error Code Taxonomy

Use this table to interpret error codes in `logs/service.log`:

| Primary Code | Secondary Code | Subsystem | Pattern Name |
|---|---|---|---|
| ERR-4001 | TIMEOUT-DB | database_pool | connection pool exhaustion |
| ERR-5002 | LOCK-WAIT | transaction_manager | deadlock |
| ERR-6003 | CACHE-MISS | cache_layer | cache stampede |
| ERR-7004 | STATE-CORRUPT | state_manager | race condition |
| ERR-8005 | CFG-MISMATCH | config_validator | config drift |

## Known Root Cause Patterns

| Pattern | Signature |
|---|---|
| connection pool exhaustion | ERR-4001 followed by TIMEOUT-DB within 5s on the same trace_id |
| deadlock | ERR-5002 followed by LOCK-WAIT on the same trace_id, recurring every 30-60s |
| cache stampede | Burst of CACHE-MISS events within 1s window followed by ERR-6003 |
| race condition | ERR-7004 with STATE-CORRUPT on different trace_ids within 100ms of each other |
| config drift | CFG-MISMATCH at startup followed by ERR-8005 on every request |

## Active Incident

- **Service**: `user-service` (port `8082`)
- **Detected pattern**: `ERR-4001 followed by TIMEOUT-DB within 5s on the same trace_id`
- **Affected subsystem**: `database_pool`
- **Root cause**: Database connection pool is too small (max_connections=2); under load all connections are consumed, subsequent requests time out waiting for a free slot.

## Fix Procedure

1. Confirm the pattern by grepping `logs/service.log` for `ERR-4001` and `TIMEOUT-DB` co-occurring on the same `trace_id`.
2. Increase max_connections in config/service.yaml and add pool recycling.
3. File to edit: `config/service.yaml`.
4. Verify: `GET /health` returns HTTP 200 and `GET` the primary endpoint no longer returns `ERR-4001`.

## Hard Requirements

1. `python src/server.py` must start and serve on `127.0.0.1:8082`.
2. `GET /health` must return HTTP 200 with `{"status":"ok"}`.
3. The primary API endpoint must return HTTP 200 (not 4xx/5xx) after the fix.
4. The fix must be minimal — change only what is necessary to address the root cause.
5. Write a one-paragraph summary to `submission/root_cause.txt` identifying:
   - The error codes observed
   - The subsystem affected
   - The root cause in plain English
   - What file/field was changed and how

## Deliverables

- Fixed `config/service.yaml` (or `src/server.py` for code-level bugs).
- `submission/root_cause.txt` — log analysis summary.
- Service must start cleanly and pass `/health` check.
