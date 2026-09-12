# GH15: Go Context String Key Type Collision

## Goal

Fix `middleware.go` so the middleware passes context values to the handler
correctly using Go's typed context key pattern.

## Requirements

1. The middleware must use the `contextKey` type (defined in `main.go`) when
   calling `context.WithValue`, not a bare string literal
2. The handler must receive the non-nil value and return HTTP 200
3. All tests pass: `go test -v ./...`
4. `go vet ./...` reports no issues

## Supporting Documents

- `middleware.go` — sets context value with wrong key type (the bug)
- `main.go` — defines `contextKey` type and `*Key` constant; handler reads value
- `main_test.go` — tests

## Contradiction / Hidden Complexity

Go's `context.Value()` compares keys by **both type and value**. Two keys
with identical underlying strings but different types are not equal:
`string("userID") ≠ contextKey("userID")`. The middleware sets a `string` key
while the handler reads a `contextKey` — they never match, so the handler
always receives `nil` and returns 500.

A naive agent may try to fix the handler instead of the middleware, or may
change the `contextKey` type to `string` (which works but removes type safety
and is not idiomatic Go).

## Important Notes

- Fix is in `middleware.go` only — change the `context.WithValue` key to use
  the `contextKey` constant already defined in `main.go`
- Do NOT modify `main.go` or `main_test.go`
- The fix is one line: use `userIDKey` (or equivalent) instead of `"userID"`
