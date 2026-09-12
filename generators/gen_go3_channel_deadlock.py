"""
Parameterized generator for GO3: Channel Deadlock.

Each seed produces a different multi-stage producer-consumer pipeline domain
(log ingestion / metrics aggregation / image processing) with 4 intentional
channel/goroutine bugs:

  Bug 1 — Unbuffered producer channel causes producer to block when the
           transform stage is busy (should be make(chan T, bufSize)).

  Bug 2 — Missing close() on the filter->sink channel means the sink goroutine
           loops forever waiting for items that will never arrive.

  Bug 3 — select{} with no default or done-channel case in the filter stage
           causes a goroutine leak when the pipeline is shut down.

  Bug 4 — WaitGroup counter mismatch: wg.Add(N) but only N-1 wg.Done() calls
           (one worker goroutine is launched without a corresponding wg.Done),
           so wg.Wait() blocks forever.

Information asymmetry:
  spec.md   — full analysis: exact locations and descriptions of all 4 bugs
  brief.md  — "fix the pipeline so all tests pass" (no specifics)
"""
from __future__ import annotations

import os
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ─────────────────────────────────────────────────────
# (domain, Item, module, source verb, transform verb, filter verb, sink noun,
#  item_field, item_value_fmt, filter_predicate_desc, filter_fn_name,
#  transform_fn_name, sink_fn_name, source_fn_name, pipeline_fn_name)

DOMAIN_CONFIGS = [
    {
        "domain": "log ingestion",
        "module": "logpipeline",
        "Item": "LogEntry",
        "item_field": "Level",
        "item_field_type": "string",
        "item_value_fmt": 'fmt.Sprintf("level-%d", i%4)',
        "item_value_examples": ["level-0", "level-1", "level-2", "level-3"],
        "source_fn": "generateLogs",
        "transform_fn": "enrichLogs",
        "filter_fn": "filterLogs",
        "sink_fn": "persistLogs",
        "pipeline_fn": "RunLogPipeline",
        "filter_predicate": 'item.Level != "level-3"',
        "filter_desc": 'entries where Level != "level-3"',
        "transform_desc": "enrich each log entry by appending a processing tag",
        "sink_desc": "persist filtered log entries to the output slice",
        "item_noun": "log entry",
        "item_noun_plural": "log entries",
        "extra_field": "Tag",
        "extra_field_type": "string",
        "extra_field_init": '""',
        "transform_extra": 'item.Tag = fmt.Sprintf("enriched-%d", item.ID)',
    },
    {
        "domain": "metrics aggregation",
        "module": "metricspipeline",
        "Item": "Metric",
        "item_field": "Name",
        "item_field_type": "string",
        "item_value_fmt": 'fmt.Sprintf("metric-%d", i%5)',
        "item_value_examples": ["metric-0", "metric-1", "metric-2", "metric-3", "metric-4"],
        "source_fn": "generateMetrics",
        "transform_fn": "normalizeMetrics",
        "filter_fn": "filterMetrics",
        "sink_fn": "aggregateMetrics",
        "pipeline_fn": "RunMetricsPipeline",
        "filter_predicate": 'item.Value > 0',
        "filter_desc": "metrics with Value > 0",
        "transform_desc": "normalize each metric by scaling its value",
        "sink_desc": "aggregate filtered metrics into the output slice",
        "item_noun": "metric",
        "item_noun_plural": "metrics",
        "extra_field": "Value",
        "extra_field_type": "float64",
        "extra_field_init": "0.0",
        "transform_extra": "item.Value = float64(item.ID) * 1.5",
    },
    {
        "domain": "image processing",
        "module": "imgpipeline",
        "Item": "ImageTask",
        "item_field": "Format",
        "item_field_type": "string",
        "item_value_fmt": 'fmt.Sprintf("fmt-%d", i%3)',
        "item_value_examples": ["fmt-0", "fmt-1", "fmt-2"],
        "source_fn": "generateImages",
        "transform_fn": "resizeImages",
        "filter_fn": "filterImages",
        "sink_fn": "saveImages",
        "pipeline_fn": "RunImagePipeline",
        "filter_predicate": 'item.Format != "fmt-2"',
        "filter_desc": 'tasks where Format != "fmt-2"',
        "transform_desc": "resize each image task by computing its scaled dimensions",
        "sink_desc": "save filtered image tasks to the output slice",
        "item_noun": "image task",
        "item_noun_plural": "image tasks",
        "extra_field": "Width",
        "extra_field_type": "int",
        "extra_field_init": "0",
        "transform_extra": "item.Width = item.ID * 64",
    },
]


class Generator(TaskGenerator):
    task_id = "GO3_channel_deadlock"
    domain = "Software Engineering"
    difficulty = "hard"
    languages = ["go"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        idx = seed % len(DOMAIN_CONFIGS)
        cfg = DOMAIN_CONFIGS[idx]

        # Seed-parameterized values
        num_items = rng.randint(12, 24)
        buf_size = rng.randint(4, 8)
        num_workers = rng.randint(2, 4)

        workspace_files = self._make_workspace(cfg, num_items, buf_size, num_workers)

        spec_md = self._gen_spec(cfg, num_items, buf_size, num_workers)
        brief_md = self._gen_brief(cfg, num_items)

        return GeneratedTask(
            task_id="GO3_channel_deadlock",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["domain"],
                "module": cfg["module"],
                "Item": cfg["Item"],
                "num_items": num_items,
                "buf_size": buf_size,
                "num_workers": num_workers,
                "bugs_fixed": [
                    "unbuffered_producer_channel",
                    "missing_close_filter_to_sink",
                    "select_no_done_case",
                    "waitgroup_counter_mismatch",
                ],
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "Software Engineering"},
        )

    # ── File generators ───────────────────────────────────────────────────────

    def _make_workspace(
        self, cfg: dict, num_items: int, buf_size: int, num_workers: int
    ) -> dict:
        files = {}
        files["main.go"] = self._gen_main_go(cfg, num_items, buf_size, num_workers)
        files["pipeline.go"] = self._gen_pipeline_go(cfg, num_items, buf_size, num_workers)
        files["pipeline_test.go"] = self._gen_test_go(cfg, num_items, buf_size, num_workers)
        files["go.mod"] = self._gen_go_mod(cfg["module"])
        return files

    def _gen_go_mod(self, module: str) -> str:
        return f"""module {module}

go 1.21
"""

    def _gen_main_go(self, cfg: dict, num_items: int, buf_size: int, num_workers: int) -> str:
        Item = cfg["Item"]
        pipeline_fn = cfg["pipeline_fn"]
        item_value_fmt = cfg["item_value_fmt"]
        item_field = cfg["item_field"]
        extra_field = cfg["extra_field"]
        extra_field_init = cfg["extra_field_init"]
        domain = cfg["domain"]
        item_noun_plural = cfg["item_noun_plural"]

        return f"""package main

import (
\t"fmt"
\t"time"
)

func main() {{
\titems := make([]{Item}, {num_items})
\tfor i := range items {{
\t\titems[i] = {Item}{{
\t\t\tID:          i + 1,
\t\t\t{item_field}: {item_value_fmt},
\t\t\t{extra_field}: {extra_field_init},
\t\t}}
\t}}

\tstart := time.Now()
\tresults, err := {pipeline_fn}(items, {num_workers})
\tif err != nil {{
\t\tfmt.Printf("{domain} pipeline error: %v\\n", err)
\t\treturn
\t}}
\telapsed := time.Since(start)
\tfmt.Printf("Processed %d {item_noun_plural} in %v\\n", len(results), elapsed.Round(time.Millisecond))
}}
"""

    def _gen_pipeline_go(
        self, cfg: dict, num_items: int, buf_size: int, num_workers: int
    ) -> str:
        Item = cfg["Item"]
        item_field = cfg["item_field"]
        item_field_type = cfg["item_field_type"]
        extra_field = cfg["extra_field"]
        extra_field_type = cfg["extra_field_type"]
        extra_field_init = cfg["extra_field_init"]
        transform_extra = cfg["transform_extra"]
        source_fn = cfg["source_fn"]
        transform_fn = cfg["transform_fn"]
        filter_fn = cfg["filter_fn"]
        sink_fn = cfg["sink_fn"]
        pipeline_fn = cfg["pipeline_fn"]
        filter_predicate = cfg["filter_predicate"]
        domain = cfg["domain"]
        item_noun = cfg["item_noun"]
        item_noun_plural = cfg["item_noun_plural"]
        transform_desc = cfg["transform_desc"]
        filter_desc = cfg["filter_desc"]
        sink_desc = cfg["sink_desc"]

        return f"""package main

import (
\t"fmt"
\t"sync"
)

// {Item} is a unit of work in the {domain} pipeline.
type {Item} struct {{
\tID          int
\t{item_field} {item_field_type}
\t{extra_field} {extra_field_type}
}}

// {source_fn} feeds {item_noun_plural} from the input slice into a channel.
// BUG 1: The source channel is unbuffered (capacity 0). When the transform
// stage is busy processing an item, the producer goroutine blocks on the
// channel send. Under concurrent load this causes the pipeline to stall and
// can deadlock if downstream consumers stop reading.
func {source_fn}(items []{Item}) <-chan {Item} {{
\t// BUG 1: should be make(chan {Item}, {buf_size}) — unbuffered channel stalls producer
\tsourceCh := make(chan {Item})
\tgo func() {{
\t\tfor _, item := range items {{
\t\t\tsourceCh <- item
\t\t}}
\t\tclose(sourceCh)
\t}}()
\treturn sourceCh
}}

// {transform_fn} reads {item_noun_plural} from in, applies the transformation
// ({transform_desc}), and forwards them to the next stage.
func {transform_fn}(in <-chan {Item}, workers int) <-chan {Item} {{
\tout := make(chan {Item}, {buf_size})
\tvar wg sync.WaitGroup
\tfor i := 0; i < workers; i++ {{
\t\twg.Add(1)
\t\tgo func() {{
\t\t\tdefer wg.Done()
\t\t\tfor item := range in {{
\t\t\t\t{transform_extra}
\t\t\t\tout <- item
\t\t\t}}
\t\t}}()
\t}}
\tgo func() {{
\t\twg.Wait()
\t\tclose(out)
\t}}()
\treturn out
}}

// {filter_fn} passes only {item_noun_plural} that satisfy the predicate
// ({filter_desc}) downstream.
// BUG 3: The select inside the goroutine has no done-channel or default case.
// When the pipeline shuts down (e.g. the caller returns early) the goroutine
// is stuck waiting on the "in" channel, leaking forever.
// BUG 4: WaitGroup counter mismatch — wg.Add(workers) but only workers-1
// goroutines call wg.Done(), so wg.Wait() blocks indefinitely.
func {filter_fn}(in <-chan {Item}, workers int) <-chan {Item} {{
\t// BUG 2: filterCh is never closed — the sink goroutine loops forever.
\tfilterCh := make(chan {Item}, {buf_size})
\tvar wg sync.WaitGroup
\tdone := make(chan struct{{}})

\tfor i := 0; i < workers; i++ {{
\t\twg.Add(1)
\t\tgo func(workerID int) {{
\t\t\t// BUG 4: only the first workers-1 goroutines defer wg.Done().
\t\t\t// The last worker (workerID == workers-1) never calls Done,
\t\t\t// so wg.Wait() below never unblocks.
\t\t\tif workerID < workers-1 {{
\t\t\t\tdefer wg.Done()
\t\t\t}}
\t\t\tfor {{
\t\t\t\t// BUG 3: select has no case for <-done, so when done is closed
\t\t\t\t// this goroutine remains blocked on "case item := <-in".
\t\t\t\tselect {{
\t\t\t\tcase item, ok := <-in:
\t\t\t\t\tif !ok {{
\t\t\t\t\t\treturn
\t\t\t\t\t}}
\t\t\t\t\tif {filter_predicate} {{
\t\t\t\t\t\tfilterCh <- item
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}
\t\t}}(i)
\t}}

\tgo func() {{
\t\twg.Wait()
\t\tclose(done)
\t\t// BUG 2: filterCh is never closed here — downstream sink loops forever
\t}}()
\treturn filterCh
}}

// {sink_fn} collects all {item_noun_plural} from the channel into a slice.
// Because filterCh is never closed (Bug 2), this function loops forever.
func {sink_fn}(in <-chan {Item}) ([]{Item}, error) {{
\tvar results []{Item}
\tfor item := range in {{
\t\tresults = append(results, item)
\t}}
\treturn results, nil
}}

// {pipeline_fn} runs the full {domain} pipeline:
//   {source_fn} -> {transform_fn} -> {filter_fn} -> {sink_fn}
func {pipeline_fn}(items []{Item}, workers int) ([]{Item}, error) {{
\tif workers < 1 {{
\t\treturn nil, fmt.Errorf("workers must be >= 1, got %d", workers)
\t}}
\tsourceCh := {source_fn}(items)
\ttransformCh := {transform_fn}(sourceCh, workers)
\tfilterCh := {filter_fn}(transformCh, workers)
\treturn {sink_fn}(filterCh)
}}
"""

    def _gen_test_go(
        self, cfg: dict, num_items: int, buf_size: int, num_workers: int
    ) -> str:
        Item = cfg["Item"]
        item_field = cfg["item_field"]
        item_value_fmt = cfg["item_value_fmt"]
        extra_field = cfg["extra_field"]
        extra_field_init = cfg["extra_field_init"]
        pipeline_fn = cfg["pipeline_fn"]
        source_fn = cfg["source_fn"]
        filter_fn = cfg["filter_fn"]
        transform_fn = cfg["transform_fn"]
        filter_predicate = cfg["filter_predicate"]
        domain = cfg["domain"]
        item_noun_plural = cfg["item_noun_plural"]

        # Compute expected count after filter (approximate — just ensure > 0 and < num_items).
        # For the test we assert len(results) > 0 and <= num_items.
        test_items_small = min(num_items, 8)

        return f"""package main

import (
\t"fmt"
\t"testing"
\t"time"
)

// makeitems builds a slice of {num_items} {item_noun_plural} for testing.
func makeItems(n int) []{Item} {{
\titems := make([]{Item}, n)
\tfor i := range items {{
\t\titems[i] = {Item}{{
\t\t\tID:          i + 1,
\t\t\t{item_field}: {item_value_fmt},
\t\t\t{extra_field}: {extra_field_init},
\t\t}}
\t}}
\treturn items
}}

// TestPipelineCompletesWithoutHang verifies the full pipeline finishes within
// the timeout. With Bug 1 (unbuffered source channel) and/or Bug 2 (missing
// close on filter channel) the pipeline hangs and this test times out.
func TestPipelineCompletesWithoutHang(t *testing.T) {{
\titems := makeItems({num_items})

\tdone := make(chan struct{{}})
\tvar results []{Item}
\tvar err error

\tgo func() {{
\t\tresults, err = {pipeline_fn}(items, {num_workers})
\t\tclose(done)
\t}}()

\tselect {{
\tcase <-done:
\t\t// pipeline finished — proceed to assertions
\tcase <-time.After(15 * time.Second):
\t\tt.Fatal("pipeline did not complete within 15s — likely deadlock or goroutine hang (check Bug 1 / Bug 2)")
\t}}

\tif err != nil {{
\t\tt.Fatalf("{pipeline_fn} returned error: %v", err)
\t}}
\tif len(results) == 0 {{
\t\tt.Fatal("pipeline produced no results")
\t}}
\tif len(results) > {num_items} {{
\t\tt.Fatalf("pipeline produced more results (%d) than input items (%d)", len(results), {num_items})
\t}}
}}

// TestSourceChannelIsBuffered verifies that the source channel returned by
// {source_fn} has a non-zero buffer. An unbuffered source channel (Bug 1)
// causes the producer goroutine to stall when the downstream stage is busy.
func TestSourceChannelIsBuffered(t *testing.T) {{
\titems := makeItems({test_items_small})

\t// Drain the channel with a slight artificial delay to simulate a slow consumer.
\t// If the source channel is unbuffered, the producer goroutine can only send
\t// one item at a time and will block; the test detects this via timeout.
\tch := {source_fn}(items)

\tgot := 0
\tdone := make(chan struct{{}})
\tgo func() {{
\t\tfor range ch {{
\t\t\tgot++
\t\t\ttime.Sleep(time.Millisecond) // simulate slow consumer
\t\t}}
\t\tclose(done)
\t}}()

\tselect {{
\tcase <-done:
\t\t// ok
\tcase <-time.After(10 * time.Second):
\t\tt.Fatal("{source_fn} timed out — source channel is likely unbuffered (Bug 1)")
\t}}
\tif got != {test_items_small} {{
\t\tt.Fatalf("expected {test_items_small} items from source, got %d", got)
\t}}
}}

// TestFilterChannelIsClosed verifies that the filter stage closes its output
// channel after all items are processed. If the channel is not closed (Bug 2)
// the downstream consumer loops forever.
func TestFilterChannelIsClosed(t *testing.T) {{
\titems := makeItems({test_items_small})
\tsourceCh := {source_fn}(items)
\ttransformCh := {transform_fn}(sourceCh, {num_workers})
\tfilterCh := {filter_fn}(transformCh, {num_workers})

\t// Drain filterCh — if it's never closed this will block forever.
\tdone := make(chan struct{{}})
\tgo func() {{
\t\tfor range filterCh {{
\t\t}}
\t\tclose(done)
\t}}()

\tselect {{
\tcase <-done:
\t\t// filter channel was closed correctly
\tcase <-time.After(10 * time.Second):
\t\tt.Fatal("filter output channel was never closed — sink hangs forever (Bug 2)")
\t}}
}}

// TestNoGoroutineLeakAfterPipeline verifies the pipeline does not leave
// goroutines blocked after completion (Bugs 3 & 4). The test runs the
// pipeline multiple times and checks it always terminates.
func TestNoGoroutineLeakAfterPipeline(t *testing.T) {{
\tfor run := 0; run < 3; run++ {{
\t\titems := makeItems({test_items_small})
\t\tdone := make(chan struct{{}})
\t\tgo func() {{
\t\t\t{pipeline_fn}(items, {num_workers}) //nolint:errcheck
\t\t\tclose(done)
\t\t}}()
\t\tselect {{
\t\tcase <-done:
\t\t\t// ok — pipeline returned cleanly
\t\tcase <-time.After(10 * time.Second):
\t\t\tt.Fatalf("run %d: pipeline did not return — goroutine leak suspected (Bug 3 / Bug 4)", run+1)
\t\t}}
\t}}
}}

// TestWaitGroupBalanced verifies the WaitGroup inside the filter stage is
// balanced. With Bug 4 the last worker goroutine never calls Done(), so
// wg.Wait() never returns — detected here via the pipeline timeout.
func TestWaitGroupBalanced(t *testing.T) {{
\t// Use a larger item set to ensure multiple workers are active simultaneously.
\titems := makeItems({num_items})
\tdone := make(chan struct{{}})
\tgo func() {{
\t\t{pipeline_fn}(items, {num_workers}) //nolint:errcheck
\t\tclose(done)
\t}}()
\tselect {{
\tcase <-done:
\t\t// wg was balanced — all workers called Done
\tcase <-time.After(15 * time.Second):
\t\tt.Fatal("WaitGroup never unblocked — likely counter mismatch (Bug 4: one goroutine missing wg.Done)")
\t}}
}}
"""

    # ── Spec / Brief generators ───────────────────────────────────────────────

    def _gen_spec(
        self, cfg: dict, num_items: int, buf_size: int, num_workers: int
    ) -> str:
        domain = cfg["domain"]
        Item = cfg["Item"]
        source_fn = cfg["source_fn"]
        transform_fn = cfg["transform_fn"]
        filter_fn = cfg["filter_fn"]
        sink_fn = cfg["sink_fn"]
        pipeline_fn = cfg["pipeline_fn"]
        item_noun_plural = cfg["item_noun_plural"]
        filter_desc = cfg["filter_desc"]
        transform_desc = cfg["transform_desc"]

        return f"""# GO3: Channel Deadlock — Full Specification (Planner Only)

## Overview

The workspace implements a four-stage {domain} pipeline in Go:

```
{source_fn} -> {transform_fn} -> {filter_fn} -> {sink_fn}
```

The pipeline processes {num_items} {item_noun_plural} through {num_workers} worker goroutines per stage. It has **four intentional concurrency bugs** in `pipeline.go` that must all be fixed. The executor only receives the brief; the planner has this full analysis.

## Program Structure

- `pipeline.go` — pipeline implementation with all 4 bugs
- `main.go` — thin driver that calls `{pipeline_fn}` and prints results
- `pipeline_test.go` — tests that detect each bug via timeout

## Pipeline Stages

| Stage | Function | Description |
|-------|----------|-------------|
| Source | `{source_fn}` | Reads items from an input slice into a channel |
| Transform | `{transform_fn}` | {transform_desc.capitalize()} |
| Filter | `{filter_fn}` | Passes only {filter_desc} |
| Sink | `{sink_fn}` | Collects results from the filter channel into a slice |

## Bug Analysis

### Bug 1 — Unbuffered Producer Channel Stalls Pipeline

**Location:** `{source_fn}()` — the `sourceCh` creation line

**Root cause:** `sourceCh := make(chan {Item})` creates an unbuffered channel.
The goroutine inside `{source_fn}` can only send one item at a time; it blocks
on each send until the transform stage is ready to receive. Under concurrent
load — or if the transform stage introduces any delay — the producer goroutine
stalls, and the entire pipeline pauses.

**Fix:** Change to a buffered channel: `make(chan {Item}, {buf_size})`

---

### Bug 2 — Missing `close()` on Filter Output Channel Causes Sink to Hang Forever

**Location:** `{filter_fn}()` — the goroutine that calls `wg.Wait()`

**Root cause:** After `wg.Wait()` returns, the goroutine closes the `done`
channel but **never calls `close(filterCh)`**. The `{sink_fn}` function drains
`filterCh` using `for item := range filterCh` — this loop never terminates
because a `range` over a channel only exits when the channel is closed.

**Fix:** Add `close(filterCh)` after `wg.Wait()` in the closing goroutine.

---

### Bug 3 — `select` Without Done-Channel Case Causes Goroutine Leak

**Location:** `{filter_fn}()` — the `select` inside each worker goroutine

**Root cause:** The `select` statement has only one case: `case item, ok := <-in`.
There is no `case <-done` arm. When the upstream channel is closed the worker
reads `ok == false` and returns — but if the pipeline is shut down early (e.g.
the caller gives up before all items are drained) and `in` is not yet closed,
the worker goroutine blocks forever on the `select`, leaking a goroutine.

**Fix:** Add a `case <-done:` arm (or replace the `select` with a direct
`for item := range in` loop, which handles channel closure automatically and
is simpler when no other signals are needed).

---

### Bug 4 — WaitGroup Counter Mismatch Blocks `wg.Wait()` Forever

**Location:** `{filter_fn}()` — the worker goroutine launch loop

**Root cause:** The loop calls `wg.Add(1)` for every worker (total: `workers`),
but only workers where `workerID < workers-1` call `defer wg.Done()`. The
last worker (`workerID == workers-1`) never calls `Done`, so `wg.Wait()` blocks
indefinitely — which in turn means `filterCh` is never closed (Bug 2 depends
on this path as well).

**Fix:** Remove the `if workerID < workers-1` guard. Every goroutine that
calls `wg.Add(1)` must have exactly one corresponding `wg.Done()`.

---

## Expected Behavior After All Fixes

- `go build ./...` succeeds with no errors
- `go vet ./...` reports no issues
- `go test -timeout 30s -v ./...` passes all five tests
- The pipeline processes all {num_items} {item_noun_plural} and exits cleanly

## Acceptance Criteria

1. `{source_fn}` creates a buffered channel (capacity ≥ 1)
2. `{filter_fn}` closes `filterCh` after all worker goroutines finish
3. Every filter worker goroutine can exit when the pipeline shuts down
4. Every goroutine that calls `wg.Add(1)` calls exactly one `wg.Done()`
5. All five tests in `pipeline_test.go` pass without timeout
6. No goroutines are leaked after the pipeline returns
"""

    def _gen_brief(self, cfg: dict, num_items: int) -> str:
        domain = cfg["domain"]
        Item = cfg["Item"]
        pipeline_fn = cfg["pipeline_fn"]
        item_noun_plural = cfg["item_noun_plural"]
        num_workers_display = 2  # representative

        return f"""# GO3: Channel Deadlock (Brief)

Fix the {domain} pipeline so all tests pass.

The pipeline processes {item_noun_plural} through four stages:
source → transform → filter → sink.

Currently the pipeline **hangs and never completes**. Running the tests will
time out instead of passing.

Run:
```
go test -timeout 30s -v ./...
```

All tests must pass within the timeout.

**Files to fix:** `pipeline.go`
**Do NOT modify:** `pipeline_test.go` or `main.go`

Follow the Planner's guidance precisely.
"""
