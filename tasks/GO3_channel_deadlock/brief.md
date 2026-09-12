# GO3: Channel Deadlock (Brief)

Fix the data processing pipeline so all tests pass.

The pipeline processes items through four stages:
**source → transform → filter → sink**

Currently the pipeline **hangs and never completes**. Running the tests times
out instead of passing.

Run:
```
go test -timeout 30s -v ./...
```

All tests must pass within the timeout.

**Files to fix:** `pipeline.go`
**Do NOT modify:** `pipeline_test.go` or `main.go`

Follow the Planner's guidance precisely.
