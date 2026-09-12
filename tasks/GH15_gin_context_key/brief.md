# GH15: Context Key Type Mismatch (Brief)

Fix the server so the middleware correctly passes values to the handler via
the request context.

Currently the handler always receives nil from the context and returns 500
instead of the expected value.

Verify with:
```
go test -v ./...
```

**Files to fix:** `middleware.go`
**Do NOT modify:** `main.go` or `main_test.go`

Follow the Planner's guidance precisely.
