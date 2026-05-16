# GH10: Fix Task Retry Backoff Calculation

The task queue's exponential backoff retry has bugs where delays become
unreasonably large or negative under certain configurations. Users report
tasks either retrying instantly (zero/negative delay) or being scheduled
days into the future.

Fix the retry logic in `task_queue.py`.
