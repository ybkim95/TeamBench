# GH298_celery_10171: Fix O(K²) message bloat in a chain of chords — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

This PR fixes O(K²) message bloat which was caused by submitting a chain of chords.

Currently, chain(chord_A, chord_B, chord_C) goes through `reduce(operator.or_, ...)` which hits `_chain.__or__` line 995, and every chord | chord nests the right chord into the left chord's body. So we get one giant chord with everything inside. 5 chords each having 10 noop tasks would require 120MB. 6 chords of the same width will require 1.4GB.

With this update, chord | chord appends flat to the chain list instead. 5 chords with 10 noop tasks require 25KB; 6 chords — 31KB.

Script to reproduce:
```python
import argparse
import json

from celery import Celery, chain, chord, group

app = Celery("repro", backend="cache+memory://")
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

@app.task
def noop(x=None):
    return None

def build_chain_of_chords(num_layers: int, tasks_per_layer: int):
    """Build chain(chord_0, chord_1, ..., chord_N) — the problematic pattern."""
    layers = []
    for _ in range(num_layers):
        header = group(noop.si() for _ in range(tasks_per_layer))
        body = noop.si()
        layers.append(chord(header, body))
    return chain(*layers)

def measure_serialized_sizes(num_layers: int, tasks_per_layer: int):
    canvas = build_chain_of_chords(num_layers, tasks_per_layer)
    canvas.freeze()

    total_bytes = 0
    print(f"\n{'Layer':<8} {'Size (bytes)':<15} {'chain entries'}")
    print("-" * 40)

    for i, task in enumerate(canvas.tasks):
        size = len(json.dumps(task.__json__()))
        total_bytes += size
        chain_entries = len(task.options.get("chain", []))
        print(f"{i:<8} {size:<15,} {chain_entries}")

    print("-" * 40)
    print(f"Total: {total_bytes:,} bytes across {len(canvas.tasks)} tasks")

    if len(canvas.tasks) >= 2:
        first = len(json.dumps(canvas.tasks[0].__json__()))
        last = len(json.dumps(canvas.tasks[-1].__json__()))
        print(f"First: {first:,}  Last: {last:,}  Ratio: {first / max(last, 1):.1f}x")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure chord-chain message sizes")
    parser.add_argument("--layers", type=int, default=8, help="Number of chord layers")
    parser.add_argument("--tasks-per-layer", type=int, default=3, help="Parallel tasks per layer")
    args = parser.parse_args()

    measure_serialized_sizes(args.layers, args.tasks_per_layer)
```

## PR Review Comments

**[user]** on `celery/canvas.py`:

The inline comment says the continuation is handled via the `chain` message option at dispatch time, but for task protocol 1 Celery uses links instead (see `prepare_steps()` selecting `use_link` based on `app.conf.task_protocol`). Could this comment be adjusted to reflect both mechanisms so it doesn’t mislead future readers/debugging?
```suggestion
                    # is handled at dispatch time (via the "chain" message option for
                    # newer task protocols, or via links when using task protocol 1),
```

**[user]** on `celery/canvas.py`:

This changes the structure produced by `chain(chord_a, chord_b, ...)` from “single nested chord” to a “flat chain of chords”. Execution semantics may remain the same, but this makes `chain(chord_a, chord_b)` diverge from `chord_a | chord_b` (and from the historical expectation that `chain(X, Y, Z)` matches `X | Y | Z`). Is that divergence intended, and if so should it be called out (docs/whatsnew) or should `chord.__or__` be aligned to avoid users seeing different behavior depending on how they compose chords?
```suggestion
                # CHAIN [last item is chord] | TASK/CHORD -> chain with chord body.
                # This keeps `chain(chord_a, chord_b, ...)` structurally aligned with
                # `chord_a | chord_b | ...`, preserving the historical expectation that
                # `chain(X, Y, Z)` matches `X | Y | Z`.
```

**[user]** on `celery/canvas.py`:

This is a significant behavior/performance fix, but I don’t see a focused regression test covering a chain of consecutive chords (e.g., asserting the chain stays flat and doesn’t nest chord bodies, and/or that the serialized payload size grows O(K) rather than O(K^2)). Could we add a unit test in `t/unit/tasks/test_canvas.py` to lock in the new composition behavior and prevent regressions?

**[user]** on `t/unit/tasks/test_canvas.py`:

`test_chain_of_chords_serialized_size_constant` only compares the serialized size of the first and last chord, but the intent reads like “constant across the whole chain”. To make this regression test harder to accidentally bypass, consider asserting that all entries are the same size (or at least that `max(sizes) == min(sizes)`), not just the endpoints.
```suggestion
        assert max(sizes) == min(sizes), (
            f"Chord sizes not constant across chain: {sizes}"
```

**[user]** on `t/integration/test_canvas.py`:

`test_chain_of_six_chords` builds a `chain(...)` with 9 `chord(...)` entries (lines 471–480). Either the test name should be updated to match what it actually covers, or the chain should be reduced to six chords to keep the test intent clear.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
