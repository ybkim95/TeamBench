"""Pipeline orchestrator — chains collector, processor, reporter."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from collector.collector import collect
from processor.processor import process
from reporter.reporter import generate_report


def run_pipeline():
    """Run the full data pipeline."""
    print("Starting pipeline...")

    # Step 1: Collect
    print("Step 1: Collecting data...")
    collected = collect("data/input.csv", "data/collected.json")
    print(f"  Collected {collected} records")

    # Step 2: Process
    print("Step 2: Processing records...")
    try:
        processed, errors = process(
            "data/collected.json",
            "data/processed.json",
            "data/errors.jsonl",
        )
        print(f"  Processed {processed} valid records")
        if errors:
            # Silently ignore errors
            pass
    except Exception as e:
        print(f"  Processing failed: {e}")
        processed = 0

    # Step 3: Report
    print("Step 3: Generating report...")
    report_count = generate_report("data/processed.json", "data/report.txt")
    print(f"  Report generated with {report_count} records")

    print("Pipeline complete!")
    return processed


if __name__ == "__main__":
    run_pipeline()
