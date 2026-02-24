# O1: Service Health Recovery (stdlib only)

## Goal
Bring up a local HTTP service that satisfies ALL requirements below.

## Hard Requirements

1. Running `bash run_service.sh` must start an HTTP server on `127.0.0.1:8080`.
2. `GET /health` must return HTTP **200**.
3. The response body must be **exactly**: `{"status":"ok"}` (no extra spaces, keys in this order).
4. `/health` must **not** emit stack traces in logs.
5. Do **not** change the endpoint paths.
6. Service must keep running for at least **8 seconds** after start.

## Deliverables
- Working code in the workspace.
- Executor must write logs to `/shared/reports/service.log`.
- Verifier must create `/shared/submission/attestation.json` with `verdict="pass"`.
