import random
from task_queue import TaskQueue, RetryPolicy, TaskState


def test_basic_retry():
    """Task retries on failure."""
    queue = TaskQueue()
    attempts = []

    def flaky_task():
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("not yet")
        return "done"

    queue.register("flaky", flaky_task, RetryPolicy(max_retries=5, base_delay=0.01, jitter=0.0))
    result = queue.submit("flaky")
    assert result.state == TaskState.SUCCESS
    assert len(attempts) == 3


def test_max_delay_cap():
    """THE BUG: Delay should never exceed max_delay."""
    policy = RetryPolicy(base_delay=1.0, max_delay=60.0, backoff_factor=2.0, jitter=0.0)

    # At attempt 20: 1.0 * 2^20 = 1048576 seconds without cap
    delay = policy.calculate_delay(attempt=20)
    assert delay <= 60.0, f"Delay {delay} exceeds max_delay 60.0"


def test_delay_never_negative():
    """THE BUG: Delay should never be negative."""
    random.seed(42)
    policy = RetryPolicy(base_delay=0.1, max_delay=10.0, backoff_factor=2.0, jitter=1.0)

    for attempt in range(10):
        delay = policy.calculate_delay(attempt)
        assert delay >= 0, f"Negative delay {delay} at attempt {attempt}"


def test_exponential_growth():
    """Delays should grow exponentially up to max_delay."""
    policy = RetryPolicy(base_delay=1.0, max_delay=100.0, backoff_factor=2.0, jitter=0.0)

    delays = [policy.calculate_delay(i) for i in range(8)]
    # Should be: 1, 2, 4, 8, 16, 32, 64, 100 (capped)
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0
    assert delays[6] == 64.0
    assert delays[7] == 100.0  # capped at max_delay


def test_jitter_bounded():
    """Jitter should not push delay above max_delay."""
    random.seed(0)
    policy = RetryPolicy(base_delay=1.0, max_delay=10.0, backoff_factor=2.0, jitter=0.5)

    for attempt in range(20):
        delay = policy.calculate_delay(attempt)
        assert 0 <= delay <= 10.0, f"Delay {delay} out of bounds at attempt {attempt}"


def test_no_jitter():
    """With jitter=0, delays are deterministic."""
    policy = RetryPolicy(base_delay=2.0, max_delay=50.0, backoff_factor=2.0, jitter=0.0)
    d1 = policy.calculate_delay(3)
    d2 = policy.calculate_delay(3)
    assert d1 == d2 == 16.0  # 2.0 * 2^3


def test_max_retries_respected():
    """Task fails after max_retries exceeded."""
    queue = TaskQueue()

    def always_fail():
        raise ValueError("always fails")

    queue.register("fail", always_fail, RetryPolicy(max_retries=2, base_delay=0.001, jitter=0.0))
    result = queue.submit("fail")
    assert result.state == TaskState.FAILED
    assert result.attempt == 3  # initial + 2 retries


def test_task_state_machine():
    """Task states transition correctly."""
    queue = TaskQueue()

    def ok():
        return "ok"

    queue.register("ok", ok, RetryPolicy())
    result = queue.submit("ok")
    assert result.state == TaskState.SUCCESS


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print(f"  PASS: {name}")
            except (AssertionError, Exception) as e:
                print(f"  FAIL: {name}: {e}")
