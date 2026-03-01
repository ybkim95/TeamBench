# CROSS1: API Contract Reconciliation

## Goal
The Python client library must correctly communicate with the Go HTTP server.
Discrepancies exist between the API spec, the server implementation, and the client.

## Requirements
1. The Go server is the source of truth — fix the Python client to match server behavior
2. Update `api_spec.yaml` to document the actual contract (matching the server)
3. All integration tests must pass: `pytest tests/`
4. The Go server must still compile: `go build ./...` (do not change Go source)

## Supporting Documents
- `service/main.go`, `service/handlers.go` — Go server (source of truth)
- `client/api.py`, `client/models.py` — Python client (has 3 bugs)
- `api_spec.yaml` — API spec (wrong in 3 places)

## The 3 Discrepancies (find them yourself)
The spec documents one version of the contract; the server implements another.
Read both and reconcile in favor of the server's actual behavior.

## Important
Do NOT modify any Go source files. Only fix:
- `client/api.py` — client request/response handling
- `client/models.py` — client data models
- `client/exceptions.py` — client exception handling
- `api_spec.yaml` — update to match actual server behavior

## Real-World Context
API contract mismatches between polyglot services are a leading cause of production
incidents. These three discrepancy patterns appear repeatedly in real migrations:
- **Field naming (camelCase vs snake_case)**: The Twitter v1 → v2 migration renamed
  hundreds of fields (e.g., `user.followers_count` → `public_metrics.followers_count`),
  silently breaking every consumer that referenced old names.
- **Pagination key rename** (`data`/`next` → `results`/`cursor`): Stripe's 2022
  changelog removed `invoice` from `Charge` objects and renamed pagination fields,
  breaking dashboard tools and analytics pipelines overnight.
- **Error format change** (HTTP 422 + `errors[]` → HTTP 400 + `error` string): The
  GitHub REST API v3 → v4 transition changed error envelopes, causing silent failures
  in CI/CD integrations that checked `response.errors[0]`.
