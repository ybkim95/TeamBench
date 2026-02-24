"""Integration tests for the data pipeline."""
import json
import os
import subprocess
import sys


def test_pipeline_end_to_end():
    """Run the full pipeline and verify outputs."""
    # Run pipeline
    result = subprocess.run(
        [sys.executable, "pipeline.py"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Check processed output
    assert os.path.isfile("data/processed.json"), "processed.json missing"
    with open("data/processed.json") as f:
        processed = json.load(f)
    assert len(processed) > 0, "No records processed"

    # Check all records have correct fields
    for rec in processed:
        assert "name" in rec, f"Missing 'name' field in {rec}"
        assert "email" in rec, f"Missing 'email' field in {rec}"
        assert "score" in rec, f"Missing 'score' field in {rec}"
        assert "processed_at" in rec, f"Missing 'processed_at' field in {rec}"

    # Check errors file exists and is valid JSONL
    assert os.path.isfile("data/errors.jsonl"), "errors.jsonl missing"
    with open("data/errors.jsonl") as f:
        errors = [json.loads(line) for line in f if line.strip()]
    assert len(errors) >= 0  # file should be parseable

    # Check report
    assert os.path.isfile("data/report.txt"), "report.txt missing"
    with open("data/report.txt") as f:
        report = f.read()
    assert len(report) > 0, "Report is empty"

    print(f"Pipeline test passed: {len(processed)} records, {len(errors)} errors")
