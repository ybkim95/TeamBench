# GO1: Concurrency Fix (Full Specification — Planner Only)

## Overview

The workspace contains a Go concurrent job processor using a worker pool pattern. The program has **three real concurrency bugs** that must be identified and fixed. The executor only sees the brief; the planner has this full analysis.

## Program Structure

`main.go` implements a `JobProcessor` struct with:
- A worker pool of N goroutines
- A `stats` map tracking per-worker completion counts
- Two mutexes: `mu1` (protects the job queue) and `mu2` (protects the stats map)
- A `results` channel for collecting completed job results
- A `processJobs(ctx)` method that orchestrates the pool

## Bug Analysis

### Bug 1 — Data Race on `stats` Map

**Location:** `worker()` function

**Description:** Each worker goroutine writes to the shared `stats` map (e.g., `p.stats[id]++`) without holding any lock. Multiple goroutines can write to the same map concurrently, which is undefined behavior in Go and is reliably detected by `go test -race`.

**Symptom:** `go test -race` reports a data race on `p.stats`. The program may also panic with `concurrent map writes`.

**Fix:** Acquire `p.mu2` before reading/writing `p.stats[id]` inside `worker()`, then release it immediately after the update. Alternatively, replace `map[int]int` with `sync.Map` and use `LoadOrStore`/`Store`.

**Correct lock ordering after fix:** mu2 is the only lock held during stats updates in workers.

### Bug 2 — Goroutine Leak via Unbuffered `results` Channel

**Location:** `processJobs()` and `worker()` functions

**Description:** The `results` channel is unbuffered (`make(chan Result)`). Workers send results with `results <- result`. When the context is cancelled, `processJobs` returns early (exits its receive loop) without draining the channel. Any worker that has already computed a result and is blocked on `results <- result` will leak forever — it can never send because no one is receiving.

**Symptom:** After context cancellation, goroutines remain live. The race detector may surface this as a goroutine leak. The program may hang under certain scheduling conditions.

**Fix (Option A — preferred):** Make the channel buffered with capacity equal to the number of jobs: `make(chan Result, numJobs)`. Workers can always send without blocking; the main goroutine drains after workers exit.

**Fix (Option B):** In `processJobs`, change the receive loop to use `select { case res := <-results: ...; case <-ctx.Done(): ... }` and then drain the channel in a separate goroutine after cancellation.

### Bug 3 — Deadlock via Inconsistent Lock Ordering

**Location:** `addJob()` acquires mu1 then mu2; `getStats()` acquires mu2 then mu1

**Description:** Classic lock-ordering deadlock. If goroutine A calls `addJob` (holds mu1, waiting for mu2) while goroutine B calls `getStats` (holds mu2, waiting for mu1), both block forever.

**Symptom:** The program deadlocks and the Go runtime prints `all goroutines are asleep - deadlock!` to stderr. Occurs non-deterministically depending on goroutine scheduling, making it appear to work sometimes.

**Fix:** Establish a canonical lock order and follow it everywhere. Choose either mu1→mu2 or mu2→mu1 and apply consistently. The simplest fix is to remove the unnecessary mu2 acquisition from `addJob` (stats are not written there) or restructure `getStats` to acquire mu1→mu2.

## Expected Behavior After Fix

```
$ go run .
All 10 jobs completed
Worker 0: 3 jobs
Worker 1: 4 jobs
Worker 2: 3 jobs

$ go test -race -count=1 ./...
ok  	jobprocessor	0.XXXs
```

- `go build ./...` succeeds
- `go vet ./...` produces no warnings
- `go test -race -count=1 -timeout 30s ./...` passes with zero races detected
- `go run .` completes within 10 seconds and prints "All 10 jobs completed"

## Acceptance Criteria

1. No data races detected by the Go race detector
2. No goroutine leaks (program exits cleanly)
3. No deadlocks (program never hangs)
4. All three test cases in `main_test.go` pass
5. The stats map is protected by a mutex in the worker function
6. Lock acquisition order is consistent between `addJob` and `getStats`
7. The `results` channel is buffered or context cancellation drains it safely
