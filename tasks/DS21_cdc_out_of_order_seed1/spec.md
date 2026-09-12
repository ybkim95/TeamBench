# DS21: CDC Out-of-Order Events

## Task
Process a Change Data Capture (CDC) stream for a user profile change data capture stream with
**88 events** across **24 user records**.
The stream contains out-of-order events — events arrive with a `arrival_time`
that does not match their logical `event_time`.

## The Problem
The naive approach processes events in `arrival_time` order. When a late-arriving
event (earlier `event_time`, later `arrival_time`) is processed after a more recent
event, it incorrectly overwrites newer state.

**Example of the bug**:
- Event A: event_time=100, UPDATE status=shipped (arrives at t=200)
- Event B: event_time=90,  UPDATE status=pending (arrives at t=210, LATE)
- Bug: B processed after A → final state: pending (WRONG, should be shipped)

## Data
File: `data/cdc_events.csv`
- `arrival_time`: Unix timestamp when event arrived in the stream
- `event_time`: Unix timestamp when the event actually occurred (logical order)
- `user_id`: entity identifier
- `op`: operation type — INSERT, UPDATE, or DELETE
- `account_status`: entity status
- `balance`: numeric value

## Requirements
1. Load `data/cdc_events.csv`
2. Sort events by **`event_time`** (not `arrival_time`) before processing
3. Apply upsert semantics with last-writer-wins:
   - For INSERT/UPDATE: only apply if `event_time >= current_record.last_event_time`
   - For DELETE: remove record from state
4. Save to `results.json`:
   - `final_record_count`: number of records in final state
   - `processing_order`: `"event_time"`
   - `upsert_semantics`: `true`
   - `final_state`: dict mapping `user_id` -> record
5. Fix `process_cdc.py`

## Deliverables
- Fixed `process_cdc.py`
- `results.json` with correct final state
