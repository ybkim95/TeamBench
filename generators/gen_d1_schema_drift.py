"""
Parameterized generator for D1: Schema Drift ETL Repair.

Each seed produces:
  - Different person names across 5 CSV batches
  - Different numeric values
  - Different column rename mappings
  - Different extra columns to drop
  - Different dedup/edge-case placement
  - Different expected output (row count, specific values, sort order)

The task structure remains the same: fix etl.py to handle schema drift.
But the specific data, column names, and expected answers change per seed.
"""
from __future__ import annotations

import csv
import io
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import (
    SeededRandom, NamePool, ValuePool, CategoryPool, ColumnSchemaGenerator,
)


class Generator(TaskGenerator):
    task_id = "D1_schema_drift"
    domain = "data"
    difficulty = "medium"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        names = NamePool(seed, count=30)
        values = ValuePool(seed + 1, low=50, high=999)
        cats = CategoryPool(seed + 2, count=5)
        schema_gen = ColumnSchemaGenerator(seed + 3)

        all_categories = cats.get_all()
        renames = schema_gen.generate_rename_map()
        extras = schema_gen.generate_extra_columns()

        # ── Generate 5 batches with progressive schema drift ──

        # Batch 1: canonical columns [id, name, value] — no category
        batch1_rows = []
        for i in range(1, 6):
            batch1_rows.append({
                "id": str(i),
                "name": names.next(),
                "value": str(values.next()),
            })

        # Batch 2: canonical + category
        batch2_rows = []
        for i in range(6, 11):
            batch2_rows.append({
                "id": str(i),
                "name": names.next(),
                "value": str(values.next()),
                "category": rng.choice(all_categories),
            })

        # Batch 3: name renamed (e.g., full_name), + category
        name_rename = renames["name"]  # e.g. "full_name"
        batch3_rows = []
        batch3_names_by_id = {}
        for i in range(11, 16):
            n = names.next()
            batch3_names_by_id[str(i)] = n
            batch3_rows.append({
                "id": str(i),
                name_rename: n,
                "value": str(values.next()),
                "category": rng.choice(all_categories),
            })

        # Batch 4: id renamed + value renamed + extra columns
        id_rename = renames["id"]  # e.g. "record_id"
        value_rename = renames["value"]  # e.g. "amount"
        extra_col = extras[0]  # e.g. "region"
        extra_values = ["west", "east", "north", "south", "central"]
        batch4_rows = []
        batch4_vals = {}
        for i in range(16, 20):
            v = values.next()
            batch4_vals[str(i)] = str(v)
            row = {
                id_rename: str(i),
                "name": names.next(),
                value_rename: str(v),
                "category": rng.choice(all_categories),
                extra_col: rng.choice(extra_values),
            }
            batch4_rows.append(row)

        # Add a duplicate of id=3 with HIGHER value (tests dedup)
        dedup_id = "3"
        dedup_value = int(batch1_rows[2]["value"]) + rng.randint(10, 100)
        dedup_cat = rng.choice(all_categories)
        batch4_rows.append({
            id_rename: dedup_id,
            "name": names.next(),
            value_rename: str(dedup_value),
            "category": dedup_cat,
            extra_col: rng.choice(extra_values),
        })

        # Batch 5: canonical + extra metadata column + edge cases
        extra_col2 = extras[-1] if len(extras) > 1 else "_metadata"
        batch5_rows = []
        batch5_normal = []
        for i in range(20, 23):
            v = values.next()
            batch5_normal.append({
                "id": str(i),
                "name": names.next(),
                "value": str(v),
                "category": rng.choice(all_categories),
                extra_col2: f"2025-01-{rng.randint(10, 28)}",
            })
        batch5_rows.extend(batch5_normal)

        # Edge case: non-numeric value
        nonnumeric_id = "23"
        batch5_rows.append({
            "id": nonnumeric_id,
            "name": names.next(),
            "value": "abc",
            "category": rng.choice(all_categories),
            extra_col2: "2025-01-20",
        })

        # Edge case: negative value
        negative_id = "24"
        batch5_rows.append({
            "id": negative_id,
            "name": names.next(),
            "value": str(-rng.randint(10, 100)),
            "category": rng.choice(all_categories),
            extra_col2: "2025-01-21",
        })

        # Edge case: duplicate of id=3 with LOWER value (should NOT replace)
        batch5_rows.append({
            "id": dedup_id,
            "name": names.next(),
            "value": str(dedup_value - rng.randint(50, 150)),
            "category": rng.choice(all_categories),
            extra_col2: "2025-01-22",
        })

        # ── Compute expected output ──
        # Merge all rows, apply transformations, compute expected result
        all_records = []

        # Batch 1 (no category → "unknown")
        for r in batch1_rows:
            all_records.append({
                "id": r["id"], "name": r["name"],
                "value": r["value"], "category": "unknown",
            })

        # Batch 2
        for r in batch2_rows:
            all_records.append({
                "id": r["id"], "name": r["name"],
                "value": r["value"], "category": r["category"],
            })

        # Batch 3 (rename name column)
        for r in batch3_rows:
            all_records.append({
                "id": r["id"], "name": r[name_rename],
                "value": r["value"], "category": r["category"],
            })

        # Batch 4 (rename id, value columns; drop extra)
        for r in batch4_rows:
            all_records.append({
                "id": r[id_rename], "name": r["name"],
                "value": r[value_rename], "category": r["category"],
            })

        # Batch 5 (drop extra column)
        for r in batch5_rows:
            all_records.append({
                "id": r["id"], "name": r["name"],
                "value": r["value"], "category": r["category"],
            })

        # Apply transformations:
        # 1. Replace non-numeric/negative values with 0
        for r in all_records:
            try:
                v = int(r["value"])
                if v < 0:
                    r["value"] = "0"
            except ValueError:
                r["value"] = "0"

        # 2. Dedup by id: keep highest value
        by_id: dict[str, dict] = {}
        for r in all_records:
            rid = r["id"]
            try:
                cur_val = int(r["value"])
            except ValueError:
                cur_val = 0
            if rid not in by_id:
                by_id[rid] = r
            else:
                try:
                    existing_val = int(by_id[rid]["value"])
                except ValueError:
                    existing_val = 0
                if cur_val > existing_val:
                    by_id[rid] = r
                elif cur_val == existing_val:
                    by_id[rid] = r  # keep last occurrence

        deduped = list(by_id.values())

        # 3. Sort by category asc, then id asc (numeric)
        deduped.sort(key=lambda r: (r["category"], int(r["id"])))

        expected_row_count = len(deduped)

        # Build expected spot-checks
        name_map = {r["id"]: r["name"] for r in deduped}
        val_map = {r["id"]: r["value"] for r in deduped}
        cat_map = {r["id"]: r["category"] for r in deduped}

        # IDs from batch 3 (renamed name column)
        batch3_check_ids = list(batch3_names_by_id.keys())[:2]
        # IDs from batch 4 (renamed id/value columns)
        batch4_check_ids = [str(i) for i in range(16, 18)]

        expected = {
            "row_count": expected_row_count,
            "columns": ["id", "name", "value", "category"],
            "dedup_id": dedup_id,
            "dedup_value": str(dedup_value),
            "dedup_category": dedup_cat,
            "nonnumeric_id": nonnumeric_id,
            "nonnumeric_expected_value": "0",
            "negative_id": negative_id,
            "negative_expected_value": "0",
            "batch3_check": {rid: batch3_names_by_id[rid] for rid in batch3_check_ids},
            "batch4_check_ids": batch4_check_ids,
            "batch4_check_values": {rid: batch4_vals[rid] for rid in batch4_check_ids},
            "batch1_missing_category_ids": [str(i) for i in range(1, 6)],
            "name_rename": name_rename,
            "id_rename": id_rename,
            "value_rename": value_rename,
            "extra_columns": extras,
        }

        # ── Generate workspace files ──

        def to_csv(rows: list[dict]) -> str:
            if not rows:
                return ""
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
            return out.getvalue()

        etl_py = self._generate_buggy_etl(name_rename, id_rename, value_rename, extras)

        workspace_files = {
            "data/input/batch_001.csv": to_csv(batch1_rows),
            "data/input/batch_002.csv": to_csv(batch2_rows),
            "data/input/batch_003.csv": to_csv(batch3_rows),
            "data/input/batch_004.csv": to_csv(batch4_rows),
            "data/input/batch_005.csv": to_csv(batch5_rows),
            "etl.py": etl_py,
        }

        # ── Generate spec and brief ──
        spec_md = self._generate_spec(
            name_rename, id_rename, value_rename, extras, expected_row_count,
        )
        brief_md = self._generate_brief()

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _generate_buggy_etl(
        self, name_rename: str, id_rename: str, value_rename: str,
        extras: list[str],
    ) -> str:
        """Generate a buggy etl.py that the agent must fix."""
        return f'''"""ETL pipeline for processing CSV batches with schema drift."""
import csv
import os
import glob


def run_etl():
    input_dir = "data/input"
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)

    all_rows = []
    for csv_file in sorted(glob.glob(os.path.join(input_dir, "*.csv"))):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append(dict(row))

    # BUG: Does not handle column renames ({name_rename} -> name, etc.)
    # BUG: Does not fill missing category with "unknown"
    # BUG: Does not handle non-numeric or negative values
    # BUG: Does not dedup by id (keep highest value)
    # BUG: Does not drop extra columns ({", ".join(extras)})
    # BUG: Does not sort output

    output_path = os.path.join(output_dir, "result.csv")
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)


if __name__ == "__main__":
    run_etl()
'''

    def _generate_spec(
        self, name_rename: str, id_rename: str, value_rename: str,
        extras: list[str], expected_row_count: int,
    ) -> str:
        extras_str = ", ".join(f"`{e}`" for e in extras)
        return f"""# D1: Schema Drift ETL Repair

## Goal
Fix the ETL pipeline so it correctly processes all input CSV files despite schema changes.

## Hard Requirements

1. The pipeline reads CSV files from `data/input/` and writes a single `data/output/result.csv`.
2. Input files have varying schemas across 5 batches with column additions, renames, and extras.
3. Column mappings:
   - `{name_rename}` must be mapped to `name`
   - `{id_rename}` must be mapped to `id`
   - `{value_rename}` must be mapped to `value`
4. Output `result.csv` must have columns: `[id, name, value, category]` -- exact order.
   - Drop any columns NOT in the canonical schema (e.g., {extras_str})
5. Missing `category` values must be filled with `"unknown"`.
6. Handle duplicate `id`s: keep the row with the HIGHER `value`. If values are equal, keep the last occurrence.
7. Rows where `value` is non-numeric or negative: replace `value` with `0`.
8. Output must be sorted by `category` ascending, then by `id` ascending (numeric sort).
9. No duplicate rows allowed (by `id`).
10. The pipeline script is `etl.py` -- run with `python etl.py`.

## Deliverables
- Fixed `etl.py` in workspace.
- Verifier must verify output schema, row count, sort order, dedup, and produce attestation.
"""

    def _generate_brief(self) -> str:
        return """# D1: Schema Drift ETL Repair (Brief)

Fix the ETL pipeline to handle schema differences across CSV batches.
The input CSVs have inconsistent schemas -- columns added, renamed, and extra columns present.
Output must be a single `data/output/result.csv`.
Run: `python etl.py`
"""
