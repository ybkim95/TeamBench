# LH3: Multi-Service Bug Fix — Payments System

## Goal
Fix all bugs across the 3-service payments system so that the
end-to-end integration test (`python run_integration_test.py`) passes completely.

## System Topology

```
service_a → service_b → service_c
```

**Topology type**: chain (Linear chain: A → B → C)

## Service Inventory

| Service | Type | Port | Description |
|---------|------|------|-------------|
| service_a | store | 8300 | Data store service |
| service_b | worker | 8101 | Background worker service |
| service_c | api | 8002 | REST API service |

## Service Interaction Contracts

Every inter-service call must use these exact contracts:

| Edge | Method | Endpoint | Content-Type | Response Field |
|------|--------|----------|--------------|----------------|
| service_a → service_b | POST | /api/validate | application/json | `status` |
| service_b → service_c | POST | /api/validate | application/json | `payload` |

### Data Schema

All services pass the following payload shape:
```json
{
  "payment_id": "<string>",
  "amount": "<value>"
}
```

Response shape from intermediate services:
```json
{
  "result": "processed",
  "record_id": "<string>",
  "amount": "<value>",
  "upstream": { ... }
}
```

Response shape from leaf services:
```json
{
  "result": "stored",
  "record_id": "<string>",
  "stored_value": "<value>"
}
```

## Bug Inventory

The following bugs are present in the system. Each service has a specific bug
that breaks the data flow. Fix **all** bugs:

- **service_a**: Has 1 bug — `wrong_response_field`
  - In `service_a/server.py`: reads `resp.get("state")` from `service_b` response but must read `"status"`
- **service_b**: Has 2 bugs — `missing_error_handling and wrong_response_field`
  - In `service_b/server.py`: upstream calls are not wrapped in try/except; add error handling that returns 503 on upstream failure
  - In `service_b/server.py`: reads `resp.get("body")` from `service_c` response but must read `"payload"`
- **service_c**: Has 1 bug — `wrong_content_type`
  - See server.py for details

## Error Handling Requirements

- Every upstream call MUST be wrapped in try/except
- Upstream failures must return HTTP 503 with `{"error": "upstream_<service>_unavailable"}`
- Invalid JSON in request body must return HTTP 400
- Unknown routes must return HTTP 404

## Grading Criteria

1. All services start without errors (each service independently runnable)
2. Health endpoint `/health` responds 200 on all services
3. Correct HTTP method on all inter-service calls
4. Correct endpoint URL on all inter-service calls
5. Correct Content-Type header on all inter-service calls
6. Correct response field name read from upstream responses
7. All upstream calls wrapped in try/except error handling
8. End-to-end POST to entry service returns 200 with correct structure
9. `record_id` and `amount` propagate through the pipeline
10. Second request also succeeds (no state corruption)
11. Malformed/missing fields handled gracefully (no 5xx crashes)
12. No new bugs introduced (existing correct logic not broken)

## Deliverables
- Fixed `<service>/server.py` for each service that has a bug
- All 3 services must pass health checks
- `python run_integration_test.py` must exit 0
