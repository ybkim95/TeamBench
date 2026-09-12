# DS21: CDC Out-of-Order Events (Brief)

Process user profile change data capture stream CDC stream.
Fix `process_cdc.py` — sort by event_time, apply upsert/last-writer-wins.
Save results to `results.json`.
