"""
Simplified Celery-inspired task queue with exponential backoff retry.

This module provides task registration, submission, and retry handling
with configurable backoff policies.
"""

import random
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class RetryPolicy:
    """
    Configures how a task should be retried on failure.

    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts before marking the task FAILED.
    base_delay : float
        Initial delay in seconds before the first retry.
    max_delay : float
        Upper bound on retry delay in seconds.
    jitter : float
        Fractional jitter applied to the computed delay to avoid
        thundering-herd effects. A value of 0.5 means ±50% of the
        pre-jitter delay may be added or subtracted.
    backoff_factor : float
        Multiplier applied at each successive attempt.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        jitter: float = 0.5,
        backoff_factor: float = 2.0,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.backoff_factor = backoff_factor

    def calculate_delay(self, attempt: int) -> float:
        """
        Return the number of seconds to wait before the next retry.

        ``attempt`` is zero-indexed: 0 = first retry, 1 = second retry, etc.
        """
        # Step 1: Exponential growth
        delay = self.base_delay * (self.backoff_factor ** attempt)

        # Step 2: Apply max_delay cap BEFORE jitter
        delay = min(delay, self.max_delay)

        # Step 3: Apply jitter based on the capped delay (not max_delay)
        jitter_amount = delay * self.jitter
        delay = delay + random.uniform(-jitter_amount, jitter_amount)

        # Step 4: Clamp final result to [0, max_delay]
        delay = max(0.0, min(delay, self.max_delay))

        return delay


class Task:
    """Represents a single task invocation, including its retry state."""

    def __init__(
        self,
        name: str,
        func: Callable,
        retry_policy: RetryPolicy,
    ) -> None:
        self.name = name
        self.func = func
        self.retry_policy = retry_policy
        self.state: TaskState = TaskState.PENDING
        self.attempt: int = 0
        self.result: Any = None
        self.last_exception: Optional[Exception] = None
        # Record computed delays for each retry (useful for testing/debugging)
        self.scheduled_delays: List[float] = []

    def execute(self, *args: Any, **kwargs: Any) -> "Task":
        """Run the task function, retrying on exception if policy allows."""
        while True:
            self.state = TaskState.RUNNING
            try:
                self.result = self.func(*args, **kwargs)
                self.state = TaskState.SUCCESS
                return self
            except Exception as exc:
                self.last_exception = exc
                self.attempt += 1
                if self.attempt > self.retry_policy.max_retries:
                    self.state = TaskState.FAILED
                    return self
                self._retry()

    def _retry(self) -> None:
        """Compute the backoff delay and transition to RETRY state."""
        delay = self.retry_policy.calculate_delay(self.attempt - 1)
        self.scheduled_delays.append(delay)
        self.state = TaskState.RETRY
        if delay > 0:
            time.sleep(delay)


class TaskQueue:
    """Registry and execution engine for named tasks."""

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        """Register a callable under ``name`` with an optional retry policy."""
        self._registry[name] = {
            "func": func,
            "retry_policy": retry_policy or RetryPolicy(),
        }

    def submit(self, name: str, *args: Any, **kwargs: Any) -> Task:
        """Create a Task for ``name`` and execute it synchronously."""
        if name not in self._registry:
            raise KeyError(f"No task registered with name {name!r}")
        entry = self._registry[name]
        task = Task(name=name, func=entry["func"], retry_policy=entry["retry_policy"])
        task.execute(*args, **kwargs)
        return task

    def get_task(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the registry entry for ``name``, or None if not found."""
        return self._registry.get(name)


def task(
    name: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 300.0,
    jitter: float = 0.5,
    backoff_factor: float = 2.0,
) -> Callable:
    """
    Decorator that registers a function as a named task on a module-level queue.

    Usage::

        @task("send_email", max_retries=5, base_delay=2.0)
        def send_email(to, subject, body):
            ...
    """
    _queue = TaskQueue()

    def decorator(func: Callable) -> Callable:
        policy = RetryPolicy(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            jitter=jitter,
            backoff_factor=backoff_factor,
        )
        _queue.register(name, func, policy)

        def wrapper(*args: Any, **kwargs: Any) -> Task:
            return _queue.submit(name, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._task_name = name
        wrapper._queue = _queue
        return wrapper

    return decorator
