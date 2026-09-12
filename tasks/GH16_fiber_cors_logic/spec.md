# GH16: CORS Middleware OR vs AND Logic Bug

## Goal

Fix `cors.go` so the CORS middleware adds headers to real cross-origin
requests (not just preflight OPTIONS requests).

## Requirements

1. A real CORS GET/POST (Origin present, no Access-Control-Request-Method)
   must receive `Access-Control-Allow-Origin` header
2. A preflight OPTIONS request (Origin + Access-Control-Request-Method both
   present) must receive CORS headers and return 204
3. A non-CORS request (no Origin header) must NOT receive CORS headers
4. An unknown/disallowed origin must NOT receive CORS headers
5. All tests pass: `go test -v ./...`

## Supporting Documents

- `cors.go` — contains the buggy `||` guard in `CORSMiddleware`
- `main.go` — server entry point and handlers (correct, do not modify)
- `main_test.go` — tests

## Contradiction / Hidden Complexity

The guard `if origin == "" || requestMethod == ""` is intended to skip
CORS processing for non-CORS requests (no Origin header). But with `||`,
real cross-origin GET requests — which have `Origin` but no
`Access-Control-Request-Method` — also match the guard and get skipped.

The fix is a single character change (`||` → `&&`), but the correct
interpretation requires understanding CORS request classification:
- Non-CORS: no Origin → skip
- Real CORS: Origin present, no request-method header → add headers
- Preflight: Origin + Access-Control-Request-Method → add headers + 204

A naive agent may try to restructure the entire middleware or add special-case
logic, missing the minimal one-character fix.

## Important Notes

- Fix is in `cors.go` — change `||` to `&&` in the guard condition
- Do NOT modify `main.go` or `main_test.go`
- The fix is exactly one character
