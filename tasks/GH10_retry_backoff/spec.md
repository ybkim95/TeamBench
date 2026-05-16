# GH10 Specification: Fix Task Retry Backoff Calculation

## Background

The `task_queue.py` module implements a Celery-inspired retry mechanism using
exponential backoff with jitter. The implementation contains three related bugs
in `RetryPolicy.calculate_delay()` that cause incorrect delay values.

## Bug Descriptions

### Issue 1: No `max_delay` cap applied

`RetryPolicy` accepts a `max_delay` parameter (default 300.0 seconds), but
`calculate_delay` never enforces it.

```
delay = base_delay * (backoff_factor ** attempt)
```

With `base_delay=1.0`, `backoff_factor=2.0`, and `attempt=30`, this yields
`1073741824` seconds — roughly 34 years. Long-running workflows with many
retry attempts silently schedule tasks arbitrarily far into the future.

**Fix**: Apply the cap before jitter: `delay = min(delay, max_delay)`.

### Issue 2: Jitter can produce negative delay

Jitter is applied using an absolute offset derived from `max_delay`, not
from the current computed delay:

```python
jitter_amount = self.max_delay * self.jitter
delay += random.uniform(-jitter_amount, jitter_amount)
```

For early retries where the base delay is small (e.g., attempt 0 with
`base_delay=0.1` gives `delay=0.1`), `jitter_amount` can be orders of
magnitude larger than `delay` (e.g., `300.0 * 0.5 = 150.0`). The random
subtraction easily drives `delay` deeply negative. A negative delay is
interpreted by the scheduler as an immediate retry with no backoff,
defeating the entire purpose of the mechanism.

**Fix**: After applying jitter, clamp: `delay = max(0.0, delay)`.

### Issue 3: Jitter applied after `max_delay` cap (wrong order)

Even if a `max_delay` cap were added naively at the end, jitter applied
after capping can push the final delay above `max_delay`:

```python
delay = min(delay, max_delay)   # capped at max_delay
delay += random.uniform(...)    # jitter pushes it above max_delay again
```

**Fix**: The correct order is:
1. Calculate base exponential: `delay = base_delay * (backoff_factor ** attempt)`
2. Apply `max_delay` cap: `delay = min(delay, max_delay)`
3. Apply jitter (additive or multiplicative) within `[0, max_delay]`
4. Clamp final result: `delay = max(0.0, min(delay, max_delay))`

## What Is Correct (Do Not Change)

- Task registration and decorator logic are correct.
- The task state machine (`PENDING → RUNNING → SUCCESS / FAILED / RETRY`) is correct.
- Retry count tracking (`attempt` incremented on each retry, task fails when
  `attempt > max_retries`) is correct.
- The `TaskQueue.submit()` synchronous execution loop is correct.
- All other `RetryPolicy` fields (`max_retries`, `base_delay`, `backoff_factor`,
  `jitter`, `max_delay`) are correctly defined; only `calculate_delay` is broken.

## Expected Behavior After Fix

| Scenario | Before fix | After fix |
|---|---|---|
| `attempt=30`, `max_delay=300` | 1,073,741,824 s | 300.0 s |
| `attempt=0`, `jitter=1.0`, bad RNG | −0.83 s | 0.0 s |
| `attempt=7`, `max_delay=100`, `jitter=0.5` | up to 192 s | ≤ 100.0 s |

The three test cases that directly exercise these bugs are:
- `test_max_delay_cap` — delay must not exceed `max_delay`
- `test_delay_never_negative` — delay must be ≥ 0
- `test_jitter_bounded` — delay must stay within `[0, max_delay]` under jitter
