# D1: Schema Drift ETL Repair (Brief)

Fix the ETL pipeline to handle schema differences across CSV batches.
The input CSVs have inconsistent schemas -- columns added, renamed, and extra columns present.
Output must be a single `data/output/result.csv`.
Run: `python etl.py`
