# INT1: Multi-Service Pipeline Repair

## Goal
Fix the data processing pipeline so it runs end-to-end correctly.

## Architecture & API Contracts

### Collector (collector/collector.py)
- Reads `data/input.csv`
- **Output format**: JSON array `[{...}, {...}]` (NOT newline-delimited JSON)
- Output file: `data/collected.json`
- Each record: `{"name": str, "email": str, "score": int, "raw_line": int}`

### Processor (processor/processor.py)
- **Input**: JSON array from collector
- Validates each record:
  - Email regex must accept `+` in local part (e.g., `user+tag@example.com`)
  - Score must be 0-100 inclusive
  - Name must be non-empty
- **Output**: normalized records with field `name` (NOT `full_name`)
- Each output record: `{"name": str, "email": str, "score": int, "processed_at": str}`
- Output file: `data/processed.json`
- Invalid records written to `data/errors.jsonl` (one JSON per line), NOT silently dropped

### Reporter (reporter/reporter.py)
- **Input**: list of processed records
- Template variables: `record.name`, `record.email`, `record.score` (NOT `record.full_name`)
- Output file: `data/report.txt`
- Records sorted by score descending in report

### Pipeline (pipeline.py)
- Orchestrates: collector → processor → reporter
- Failed records must be logged to `data/errors.jsonl`, NOT silently dropped
- End-to-end: 20 input records → 18 valid output records (2 have genuinely invalid data)

## Deliverables
- Fixed pipeline that passes integration test
- `data/processed.json` with 18 records
- `data/errors.jsonl` with 2 error entries
- `data/report.txt` with formatted report
