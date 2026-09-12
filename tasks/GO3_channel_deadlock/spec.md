# GO3: Channel Deadlock — Full Specification (Planner Only)

## Overview

The workspace implements a four-stage data processing pipeline in Go. It has
**four intentional concurrency bugs** in `pipeline.go` that must all be fixed.
The executor only receives the brief; the planner has this full analysis.

## Pipeline Architecture

```
source stage -> transform stage -> filter stage -> sink stage
```

Each stage communicates via Go channels. The transform and filter stages use
a worker pool (`workers` goroutines each). The sink collects all results into
a slice.

## Bug Analysis

### Bug 1 — Unbuffered Producer Channel Stalls Pipeline

**Location:** The source function — the channel creation line

**Root cause:** The source channel is created with `make(chan T)` (unbuffered,
capacity 0). The goroutine feeding items into the source channel can only send
one item at a time; it blocks on each send until the transform stage is ready
to receive. Under any scheduling delay or concurrent load the producer goroutine
stalls, causing the entire pipeline to pause or deadlock.

**Fix:** Change the source channel creation to use a buffer:
`make(chan T, bufSize)` where bufSize matches the value in the original call.

---

### Bug 2 — Missing `close()` on Filter Output Channel Causes Sink to Hang

**Location:** The filter function — the goroutine that calls `wg.Wait()`

**Root cause:** After `wg.Wait()` returns, the goroutine closes an internal
done channel but **never calls `close(filterCh)`**. The sink function drains
the filter channel using `for item := range filterCh` — this loop never
terminates because a `range` over a channel only exits when the channel is
closed. The entire pipeline hangs forever at the sink.

**Fix:** Add `close(filterCh)` immediately after `wg.Wait()` in the closing
goroutine inside the filter function.

---

### Bug 3 — `select` Without Done-Channel Case Causes Goroutine Leak

**Location:** The filter function — the `select` statement inside each worker
goroutine

**Root cause:** The `select` has only one case: receiving from the input
channel. There is no `case <-done` arm. When the pipeline shuts down early
(before all upstream items are drained) the worker goroutine blocks forever
on the `select`, leaking a goroutine that can never exit.

**Fix:** Add a `case <-done: return` arm to the select so each worker can
exit when signalled, OR replace the `select` with a simple
`for item := range in` loop (which exits automatically when the channel closes
and is the idiomatic Go approach when no other exit signal is needed).

---

### Bug 4 — WaitGroup Counter Mismatch Blocks `wg.Wait()` Forever

**Location:** The filter function — the worker goroutine launch loop

**Root cause:** The loop calls `wg.Add(1)` for every worker, but only workers
whose ID is less than `workers-1` call `defer wg.Done()`. The last worker
(ID == `workers-1`) never decrements the counter, so `wg.Wait()` blocks
indefinitely — which means the filter output channel is never closed, and the
sink hangs forever (Bug 2 is compounded by this).

**Fix:** Remove the `if workerID < workers-1` conditional guard entirely. Every
goroutine that calls `wg.Add(1)` must have exactly one corresponding `wg.Done()`.

---

## Expected Behavior After All Fixes

- `go build ./...` succeeds with no errors
- `go vet ./...` reports no issues
- `go test -timeout 30s -v ./...` passes all tests
- The pipeline processes all input items and exits cleanly

## Acceptance Criteria

1. The source stage creates a **buffered** channel (capacity ≥ 1)
2. The filter stage **closes** its output channel after all worker goroutines finish
3. Every filter worker goroutine has a path to exit when the pipeline shuts down
4. Every `wg.Add(1)` call has exactly one corresponding `wg.Done()`
5. All tests in `pipeline_test.go` pass without timing out
6. No goroutines are leaked after the pipeline returns
