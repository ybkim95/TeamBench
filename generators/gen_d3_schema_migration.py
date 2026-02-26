"""
Parameterized generator for D3: Database Schema Migration.

Each seed produces:
  - Different table name (drawn from a pool)
  - Different column renames (old_col -> new_col)
  - Different data types added / constraints added
  - Different number of seed rows in the v1 SQLite database
  - Different expected v2 schema and data preservation checks

The scenario: Write a migration script (migration.py) that transforms a SQLite
database from v1 schema to v2.  The spec (visible to the Planner) gives the
full ordered migration plan; the brief (visible to the Executor) just says to
implement the migration.

Migration steps always follow the safe order:
  1. Add new nullable columns
  2. Backfill / migrate data into new columns
  3. Drop old columns  (SQLite requires recreate-table trick)
  4. Add constraints / indexes

Wrong step order causes data loss — this is the core challenge (Pattern D,F).
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import os
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom, NamePool, ValuePool


# ── Domain pools ─────────────────────────────────────────────────────────────

TABLE_NAMES = [
    "employees", "customers", "products", "orders", "invoices",
    "accounts", "contacts", "assets", "tickets", "projects",
    "subscriptions", "shipments", "transactions", "vendors", "devices",
]

# Each entry: (old_name_col, new_name_col, old_email_col, new_email_col,
#              old_status_col, new_status_col, old_amount_col, new_amount_col)
COLUMN_RENAME_SETS = [
    ("full_name",    "name",         "email_address", "email",     "account_status", "status",  "total_amount",  "amount"),
    ("display_name", "username",     "contact_email", "email",     "record_status",  "active",  "gross_value",   "value"),
    ("person_name",  "first_name",   "user_email",    "email",     "entry_state",    "enabled", "sale_amount",   "price"),
    ("employee_name","full_name",    "work_email",    "email",     "emp_status",     "status",  "salary_amount", "salary"),
    ("client_name",  "name",         "client_email",  "email",     "client_status",  "active",  "contract_value","value"),
    ("item_name",    "title",        "item_email",    "contact",   "item_status",    "status",  "item_price",    "price"),
    ("account_name", "display_name", "account_email", "email",     "acct_status",    "state",   "acct_balance",  "balance"),
]

STATUS_DOMAINS = [
    (["active", "inactive", "pending"],         "active"),
    (["enabled", "disabled", "suspended"],      "enabled"),
    (["open", "closed", "archived"],            "open"),
    (["live", "paused", "terminated"],          "live"),
    (["approved", "rejected", "under_review"],  "approved"),
]

CONSTRAINT_TYPES = [
    ("NOT NULL",   "not_null"),
    ("UNIQUE",     "unique"),
    ("NOT NULL",   "not_null"),
    ("CHECK",      "check"),
    ("NOT NULL",   "not_null"),
]

NEW_COLUMN_SETS = [
    [("created_at", "TEXT", "2024-01-01"),  ("updated_at", "TEXT", "2024-01-01")],
    [("created_date", "TEXT", "2024-01-01"), ("score", "INTEGER", "0")],
    [("region", "TEXT", "unknown"),         ("tier", "TEXT", "standard")],
    [("priority", "INTEGER", "1"),          ("tags", "TEXT", "")],
    [("country", "TEXT", "US"),             ("language", "TEXT", "en")],
]


class Generator(TaskGenerator):
    task_id = "D3_schema_migration"
    domain = "data"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        names = NamePool(seed, count=40)
        values = ValuePool(seed + 1, low=1000, high=99999)

        # ── Pick seed-specific schema parameters ──────────────────────────
        table = rng.choice(TABLE_NAMES)

        rename_set = rng.choice(COLUMN_RENAME_SETS)
        (old_name, new_name, old_email, new_email,
         old_status, new_status, old_amount, new_amount) = rename_set

        status_vals, default_status = rng.choice(STATUS_DOMAINS)
        new_cols = rng.choice(NEW_COLUMN_SETS)   # list of (col, type, default)

        num_rows = rng.randint(8, 15)
        num_steps = rng.randint(4, 6)  # how many steps in migration plan (4-6)

        # ── Build v1 rows ─────────────────────────────────────────────────
        v1_rows = []
        for i in range(1, num_rows + 1):
            v1_rows.append({
                "id": i,
                old_name: names.next(),
                old_email: f"user{i}@example.com",
                old_status: rng.choice(status_vals),
                old_amount: values.next(),
            })

        # ── Compute expected v2 state ─────────────────────────────────────
        # After migration:
        #   - old_name  -> new_name  (rename)
        #   - old_email -> new_email (rename)
        #   - old_status -> new_status (rename)
        #   - old_amount -> new_amount (rename)
        #   - new extra columns added with defaults
        #   - row count unchanged

        v2_rows = []
        for r in v1_rows:
            row = {
                "id": r["id"],
                new_name: r[old_name],
                new_email: r[old_email],
                new_status: r[old_status],
                new_amount: r[old_amount],
            }
            for (col, col_type, default) in new_cols:
                if col_type == "INTEGER":
                    row[col] = int(default)
                else:
                    row[col] = default
            v2_rows.append(row)

        # Spot-check IDs (first 3, last 1)
        spot_ids = [r["id"] for r in v1_rows[:3]] + [v1_rows[-1]["id"]]
        spot_ids = list(dict.fromkeys(spot_ids))  # deduplicate, preserve order

        spot_checks = {}
        for sid in spot_ids:
            src = next(r for r in v1_rows if r["id"] == sid)
            spot_checks[str(sid)] = {
                "old_name_val":   src[old_name],
                "old_email_val":  src[old_email],
                "old_status_val": src[old_status],
                # Store as string: SQLite returns TEXT after table-recreate migration
                "old_amount_val": str(src[old_amount]),
            }

        v2_columns = (
            ["id", new_name, new_email, new_status, new_amount]
            + [c[0] for c in new_cols]
        )

        expected = {
            "table": table,
            "row_count": num_rows,
            "v2_columns": v2_columns,
            "old_columns": [old_name, old_email, old_status, old_amount],
            "new_columns_added": [c[0] for c in new_cols],
            "new_columns_defaults": {c[0]: c[2] for c in new_cols},
            "renames": {
                old_name:   new_name,
                old_email:  new_email,
                old_status: new_status,
                old_amount: new_amount,
            },
            "spot_checks": spot_checks,
            "status_values": status_vals,
            "default_status": default_status,
        }

        # ── Build v1 SQLite database as bytes ─────────────────────────────
        db_bytes = self._build_v1_db(table, v1_rows, old_name, old_email,
                                     old_status, old_amount)

        # ── Generate migration.py skeleton ────────────────────────────────
        migration_py = self._generate_migration_skeleton(
            table, old_name, new_name, old_email, new_email,
            old_status, new_status, old_amount, new_amount,
            new_cols, num_steps,
        )

        # ── Generate spec and brief ───────────────────────────────────────
        spec_md = self._generate_spec(
            table, old_name, new_name, old_email, new_email,
            old_status, new_status, old_amount, new_amount,
            new_cols, num_rows, num_steps, status_vals,
        )
        brief_md = self._generate_brief(table)

        workspace_files: dict[str, str | bytes] = {
            "database.db": db_bytes,
            "migration.py": migration_py,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_v1_db(
        self,
        table: str,
        rows: list[dict],
        old_name: str,
        old_email: str,
        old_status: str,
        old_amount: str,
    ) -> bytes:
        """Build a v1 SQLite database in memory and return as bytes."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            conn = sqlite3.connect(tmp_path)
            cur = conn.cursor()
            cur.execute(f"""
                CREATE TABLE {table} (
                    id INTEGER PRIMARY KEY,
                    {old_name} TEXT NOT NULL,
                    {old_email} TEXT NOT NULL,
                    {old_status} TEXT NOT NULL DEFAULT 'active',
                    {old_amount} INTEGER NOT NULL DEFAULT 0
                )
            """)
            for r in rows:
                cur.execute(
                    f"INSERT INTO {table} (id, {old_name}, {old_email}, {old_status}, {old_amount}) "
                    f"VALUES (?, ?, ?, ?, ?)",
                    (r["id"], r[old_name], r[old_email], r[old_status], r[old_amount]),
                )
            conn.commit()
            conn.close()

            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)

    def _generate_migration_skeleton(
        self,
        table: str,
        old_name: str, new_name: str,
        old_email: str, new_email: str,
        old_status: str, new_status: str,
        old_amount: str, new_amount: str,
        new_cols: list[tuple],
        num_steps: int,
    ) -> str:
        new_cols_repr = repr(new_cols)
        return f'''"""
Database migration script: v1 -> v2 schema for table `{table}`.

Run with: python migration.py

The migration MUST follow the safe step order to avoid data loss:
  1. Add new nullable columns
  2. Backfill / migrate data into new columns
  3. Drop old columns (SQLite requires table-recreate approach)
  4. Add constraints / indexes

TODO: Implement each step below.
"""
import sqlite3
import os

DB_PATH = "database.db"


def migrate(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # TODO Step 1: Add new columns (nullable so existing rows are unaffected)
    # New columns to add: {new_cols_repr}
    # Example: cur.execute("ALTER TABLE {table} ADD COLUMN col_name TEXT")

    # TODO Step 2: Backfill / migrate data
    # Rename semantics:
    #   {old_name}   -> {new_name}
    #   {old_email}  -> {new_email}
    #   {old_status} -> {new_status}
    #   {old_amount} -> {new_amount}
    # SQLite does not support RENAME COLUMN in older versions; use table-recreate.

    # TODO Step 3: Drop old columns by recreating the table with the new schema
    # New schema must have: id, {new_name}, {new_email}, {new_status}, {new_amount}
    # plus any newly added columns.

    # TODO Step 4: Add constraints / indexes as needed
    # Example: CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_{new_email} ON {table}({new_email})

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
'''

    def _generate_spec(
        self,
        table: str,
        old_name: str, new_name: str,
        old_email: str, new_email: str,
        old_status: str, new_status: str,
        old_amount: str, new_amount: str,
        new_cols: list[tuple],
        num_rows: int,
        num_steps: int,
        status_vals: list[str],
    ) -> str:
        new_cols_lines = "\n".join(
            f"   - `{col}` {typ} (default: `{default!r}`)"
            for col, typ, default in new_cols
        )
        status_vals_str = ", ".join(f'`"{v}"`' for v in status_vals)
        step_count = max(4, min(num_steps, 6))

        steps_block = f"""### Migration Steps (must be executed in this exact order)

**Step 1 — Add new nullable columns**
Add the following columns to `{table}` without touching existing data:
{new_cols_lines}

**Step 2 — Migrate / rename column data**
Copy data from old columns into new column names so nothing is lost:
- `{old_name}`   → `{new_name}`
- `{old_email}`  → `{new_email}`
- `{old_status}` → `{new_status}`
- `{old_amount}` → `{new_amount}`

Note: SQLite does not support `ALTER TABLE ... RENAME COLUMN` in all versions.
Use the table-recreate approach: CREATE new table, INSERT ... SELECT, DROP old, RENAME new.

**Step 3 — Drop old columns**
Remove the old column names by completing the table-recreate from Step 2.
Old columns to eliminate: `{old_name}`, `{old_email}`, `{old_status}`, `{old_amount}`.

**Step 4 — Add constraints and indexes**
After the schema is clean, add:
- `NOT NULL` constraint on `{new_name}` and `{new_email}`
- A unique index on `{new_email}`: `CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_{new_email} ON {table}({new_email})`
"""
        if step_count >= 5:
            steps_block += f"""
**Step 5 — Validate row count**
Assert that `SELECT COUNT(*) FROM {table}` equals the original row count ({num_rows}).
Raise an exception and roll back if counts differ.
"""
        if step_count >= 6:
            steps_block += f"""
**Step 6 — Write migration attestation**
Write `migration_result.json` to the workspace directory with:
```json
{{
  "table": "{table}",
  "rows_migrated": {num_rows},
  "verdict": "pass"
}}
```
"""

        return f"""# D3: Database Schema Migration

## Goal
Implement `migration.py` so it safely migrates the SQLite database (`database.db`)
from v1 schema to v2 schema for the `{table}` table.

## v1 Schema (current)

```sql
CREATE TABLE {table} (
    id         INTEGER PRIMARY KEY,
    {old_name}   TEXT NOT NULL,
    {old_email}  TEXT NOT NULL,
    {old_status} TEXT NOT NULL DEFAULT 'active',
    {old_amount} INTEGER NOT NULL DEFAULT 0
);
```

The database currently contains **{num_rows} rows**.
Status values in use: {status_vals_str}.

## v2 Schema (target)

```sql
CREATE TABLE {table} (
    id         INTEGER PRIMARY KEY,
    {new_name}   TEXT NOT NULL,
    {new_email}  TEXT NOT NULL UNIQUE,
    {new_status} TEXT NOT NULL DEFAULT 'active',
    {new_amount} INTEGER NOT NULL DEFAULT 0,
{chr(10).join(f"    {col}   {typ}," for col, typ, _ in new_cols)}
);
```

## Hard Requirements

1. **No data loss**: Every row in v1 must be present in v2 with the same `id`.
2. **Column renames**: Map old column names to new ones exactly:
   - `{old_name}` → `{new_name}`
   - `{old_email}` → `{new_email}`
   - `{old_status}` → `{new_status}`
   - `{old_amount}` → `{new_amount}`
3. **New columns**: Add with the specified defaults; existing rows get the default value.
4. **Row count**: `SELECT COUNT(*) FROM {table}` must equal {num_rows} after migration.
5. **Step order**: Follow the safe migration order below — wrong order causes data loss.
6. **Atomic**: Wrap all DDL/DML in a transaction; roll back on any error.
7. **Idempotent**: Running `migration.py` twice must not crash or corrupt data.
8. **Script**: Run with `python migration.py` from the workspace directory.

{steps_block}

## Rollback Strategy

If any step fails:
- Roll back the transaction (`conn.rollback()`)
- Restore the original table (keep a backup as `{table}_backup` before Step 3)
- Print an error message and exit with code 1

## Deliverables
- Completed `migration.py` in the workspace.
- Verifier must confirm: migration runs without error, v2 schema correct, row count
  unchanged, column renames applied, new columns present with defaults, data preserved,
  unique index on `{new_email}`, and produce an attestation file.
"""

    def _generate_brief(self, table: str) -> str:
        return f"""# D3: Database Schema Migration (Brief)

Write a migration script for the `{table}` database table.
The Planner has the full migration plan with the correct step order and rollback strategy.

Run with: `python migration.py`
"""
