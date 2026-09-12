# GH16: CORS Middleware Logic Bug (Brief)

Fix the CORS middleware so browsers can make cross-origin requests.

Currently real cross-origin GET/POST requests (with an Origin header) do not
receive CORS headers — only preflight OPTIONS requests work correctly.

Verify with:
```
go test -v ./...
```

**Files to fix:** `cors.go`
**Do NOT modify:** `main.go` or `main_test.go`

Follow the Planner's guidance precisely.
