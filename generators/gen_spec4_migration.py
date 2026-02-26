"""
Parameterized generator for SPEC4: Database Schema Migration (Hard).

TNI Pattern D,F — The spec contains the full before-schema, after-schema,
migration constraints, and rollback requirements. The brief says only
"write the migration script."

Each seed varies:
  - Table names (drawn from a domain-specific pool)
  - Column additions (new columns with specific types and NULL semantics)
  - Column renames (old -> new)
  - Type changes (e.g., INTEGER -> REAL for a monetary column)
  - New indexes (UNIQUE, plain, composite)
  - FK addition (reference to a second table)
  - Number of seed rows
  - Rollback file name

Migration constraints enforced by the spec:
  1. Add new nullable columns BEFORE migrating data
  2. Migrate / backfill data (type coercions, renames via table-recreate)
  3. Create indexes AFTER data migration
  4. FK added via table-recreate with FOREIGN KEY clause
  5. All steps wrapped in a single transaction; roll back on error

Grader: 12 checks (migration runs, schema correct, row count preserved,
data preserved, old columns gone, new columns with defaults, unique index,
FK present in schema, type coercion correct, no data loss, idempotent re-run,
attestation file).
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom, NamePool, ValuePool

# ── Domain pools ─────────────────────────────────────────────────────────────

TABLE_NAMES = [
    "employees", "customers", "products", "orders", "contracts",
    "accounts", "suppliers", "assets", "tickets", "projects",
    "subscriptions", "shipments", "transactions", "vendors", "devices",
    "memberships", "listings", "campaigns", "incidents", "invoices",
]

# Second (reference) table name paired with the main table
REF_TABLE_NAMES = [
    "departments", "regions", "categories", "teams", "divisions",
    "locations", "segments", "groups", "units", "sectors",
    "channels", "tiers", "clusters", "zones", "pools",
    "branches", "portfolios", "offices", "sections", "squads",
]

# Column rename sets: (old_label, new_label, old_contact, new_contact,
#                     old_state, new_state, old_value_col, new_value_col)
COLUMN_RENAME_SETS = [
    ("full_name",     "name",          "email_address",  "email",
     "account_status","status",        "total_amount",   "amount"),
    ("display_name",  "username",      "contact_email",  "email",
     "record_status", "active",        "gross_value",    "value"),
    ("person_name",   "first_name",    "user_email",     "email",
     "entry_state",   "enabled",       "sale_amount",    "price"),
    ("employee_name", "full_name",     "work_email",     "email",
     "emp_status",    "status",        "salary_amount",  "salary"),
    ("client_name",   "name",          "client_email",   "email",
     "client_status", "active",        "contract_value", "value"),
    ("item_name",     "title",         "item_contact",   "contact",
     "item_status",   "status",        "item_price",     "price"),
    ("account_name",  "display_name",  "account_email",  "email",
     "acct_status",   "state",         "acct_balance",   "balance"),
    ("record_name",   "label",         "record_contact", "contact",
     "record_state",  "state",         "record_value",   "value"),
]

STATUS_DOMAINS = [
    (["active", "inactive", "pending"],         "active"),
    (["enabled", "disabled", "suspended"],      "enabled"),
    (["open", "closed", "archived"],            "open"),
    (["live", "paused", "terminated"],          "live"),
    (["approved", "rejected", "under_review"],  "approved"),
    (["new", "processing", "complete"],         "new"),
    (["draft", "published", "retired"],         "draft"),
]

# New columns added: list of (col_name, sql_type, python_default, sql_default_expr)
NEW_COLUMN_SETS = [
    [
        ("created_at",  "TEXT",    "2024-01-01",  "'2024-01-01'"),
        ("updated_at",  "TEXT",    "2024-01-01",  "'2024-01-01'"),
    ],
    [
        ("created_date","TEXT",    "2024-01-01",  "'2024-01-01'"),
        ("score",       "INTEGER", "0",           "0"),
    ],
    [
        ("region",      "TEXT",    "unknown",     "'unknown'"),
        ("tier",        "TEXT",    "standard",    "'standard'"),
    ],
    [
        ("priority",    "INTEGER", "1",           "1"),
        ("tags",        "TEXT",    "",            "''"),
    ],
    [
        ("country",     "TEXT",    "US",          "'US'"),
        ("language",    "TEXT",    "en",          "'en'"),
    ],
    [
        ("notes",       "TEXT",    "",            "''"),
        ("version",     "INTEGER", "1",           "1"),
    ],
    [
        ("source",      "TEXT",    "manual",      "'manual'"),
        ("weight",      "INTEGER", "0",           "0"),
    ],
]

# Type-change sets: (old_type, new_type, coerce_expr)
# coerce_expr is a Python expression: lambda val -> new_val (as string for round-trip)
TYPE_CHANGE_OPTIONS = [
    # amount column: INTEGER -> REAL (multiply by 1.0)
    ("INTEGER", "REAL", lambda v: float(v)),
    # same: keep INTEGER (no type change for variety)
    ("INTEGER", "INTEGER", lambda v: int(v)),
    ("INTEGER", "REAL", lambda v: float(v)),
    ("INTEGER", "INTEGER", lambda v: int(v)),
    ("INTEGER", "REAL", lambda v: float(v)),
    ("INTEGER", "INTEGER", lambda v: int(v)),
    ("INTEGER", "REAL", lambda v: float(v)),
    ("INTEGER", "INTEGER", lambda v: int(v)),
]

# Index sets: list of (index_name_suffix, col_expr, unique)
INDEX_OPTION_SETS = [
    [("email_uniq",    "{email}",          True),
     ("status_idx",    "{state}",          False)],
    [("contact_uniq",  "{contact}",        True),
     ("created_idx",   "created_at",       False)],
    [("label_uniq",    "{label}",          True),
     ("priority_idx",  "priority",         False)],
    [("email_uniq",    "{email}",          True),
     ("region_idx",    "region",           False)],
    [("contact_uniq",  "{contact}",        True),
     ("score_idx",     "score",            False)],
    [("label_uniq",    "{label}",          True),
     ("country_idx",   "country",          False)],
    [("email_uniq",    "{email}",          True),
     ("version_idx",   "version",          False)],
]


class Generator(TaskGenerator):
    task_id = "SPEC4_migration"
    domain = "data"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        names = NamePool(seed, count=50)
        values = ValuePool(seed + 1, low=1000, high=99999)

        # ── Pick seed-specific parameters ────────────────────────────────
        table = rng.choice(TABLE_NAMES)
        # Ensure ref_table differs from table
        ref_table = rng.choice([t for t in REF_TABLE_NAMES if t != table])

        rename_set = rng.choice(COLUMN_RENAME_SETS)
        (old_label, new_label, old_contact, new_contact,
         old_state, new_state, old_value_col, new_value_col) = rename_set

        status_vals, default_status = rng.choice(STATUS_DOMAINS)
        new_cols = rng.choice(NEW_COLUMN_SETS)
        type_change = rng.choice(TYPE_CHANGE_OPTIONS)
        old_value_type, new_value_type, coerce_fn = type_change
        index_set = rng.choice(INDEX_OPTION_SETS)

        num_rows = rng.randint(8, 18)
        num_ref_rows = rng.randint(3, 6)

        # ── Build reference table rows ────────────────────────────────────
        ref_rows = [{"id": i, "name": f"ref_{i}"} for i in range(1, num_ref_rows + 1)]

        # ── Build v1 rows ─────────────────────────────────────────────────
        v1_rows = []
        for i in range(1, num_rows + 1):
            ref_id = rng.randint(1, num_ref_rows)
            raw_amount = values.next()
            v1_rows.append({
                "id": i,
                old_label: names.next(),
                old_contact: f"user{i}@example.com",
                old_state: rng.choice(status_vals),
                old_value_col: raw_amount,
                "ref_id": ref_id,
            })

        # ── Compute v2 expected values ────────────────────────────────────
        # After migration:
        #   - old columns renamed
        #   - value column type changed (INTEGER -> new_value_type)
        #   - new columns added with defaults
        #   - indexes created
        #   - FK on ref_id referencing ref_table(id)

        v2_rows = []
        for r in v1_rows:
            row = {
                "id": r["id"],
                new_label: r[old_label],
                new_contact: r[old_contact],
                new_state: r[old_state],
                new_value_col: coerce_fn(r[old_value_col]),
                "ref_id": r["ref_id"],
            }
            for (col, sql_type, py_default, _sql_default) in new_cols:
                if sql_type == "INTEGER":
                    row[col] = int(py_default)
                else:
                    row[col] = py_default
            v2_rows.append(row)

        # Spot-checks: first 3 + last row
        spot_ids = [r["id"] for r in v1_rows[:3]] + [v1_rows[-1]["id"]]
        spot_ids = list(dict.fromkeys(spot_ids))

        spot_checks = {}
        for sid in spot_ids:
            src = next(r for r in v1_rows if r["id"] == sid)
            spot_checks[str(sid)] = {
                "label_val":   src[old_label],
                "contact_val": src[old_contact],
                "state_val":   src[old_state],
                "value_val":   coerce_fn(src[old_value_col]),
                "ref_id":      src["ref_id"],
            }

        # Resolve index column names (substitute placeholders)
        def resolve_idx(col_expr: str) -> str:
            return (col_expr
                    .replace("{email}", new_contact)
                    .replace("{contact}", new_contact)
                    .replace("{label}", new_label)
                    .replace("{state}", new_state))

        resolved_indexes = []
        for (suffix, col_expr, unique) in index_set:
            col = resolve_idx(col_expr)
            # Only include index if the column actually exists in v2
            v2_all_cols = (
                ["id", new_label, new_contact, new_state, new_value_col, "ref_id"]
                + [c[0] for c in new_cols]
            )
            if col in v2_all_cols:
                resolved_indexes.append({
                    "name": f"idx_{table}_{suffix}",
                    "col": col,
                    "unique": unique,
                })

        v2_columns = (
            ["id", new_label, new_contact, new_state, new_value_col, "ref_id"]
            + [c[0] for c in new_cols]
        )

        expected = {
            "table": table,
            "ref_table": ref_table,
            "row_count": num_rows,
            "v2_columns": v2_columns,
            "old_columns": [old_label, old_contact, old_state, old_value_col],
            "new_columns_added": [c[0] for c in new_cols],
            "new_columns_defaults": {c[0]: c[2] for c in new_cols},
            "renames": {
                old_label:     new_label,
                old_contact:   new_contact,
                old_state:     new_state,
                old_value_col: new_value_col,
            },
            "value_col_type_change": {
                "col": new_value_col,
                "old_type": old_value_type,
                "new_type": new_value_type,
            },
            "indexes": resolved_indexes,
            "fk": {
                "col": "ref_id",
                "ref_table": ref_table,
                "ref_col": "id",
            },
            "spot_checks": spot_checks,
            "status_values": status_vals,
            "default_status": default_status,
        }

        # ── Build workspace files ─────────────────────────────────────────
        db_bytes = self._build_v1_db(
            table, ref_table, v1_rows, ref_rows,
            old_label, old_contact, old_state, old_value_col,
            old_value_type, status_vals,
        )

        migration_py = self._generate_migration_skeleton(
            table, ref_table,
            old_label, new_label,
            old_contact, new_contact,
            old_state, new_state,
            old_value_col, new_value_col,
            old_value_type, new_value_type,
            new_cols, resolved_indexes,
        )

        spec_md = self._generate_spec(
            table, ref_table,
            old_label, new_label,
            old_contact, new_contact,
            old_state, new_state,
            old_value_col, new_value_col,
            old_value_type, new_value_type,
            new_cols, num_rows, status_vals, resolved_indexes,
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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_v1_db(
        self,
        table: str,
        ref_table: str,
        v1_rows: list[dict],
        ref_rows: list[dict],
        old_label: str,
        old_contact: str,
        old_state: str,
        old_value_col: str,
        old_value_type: str,
        status_vals: list[str],
    ) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            conn = sqlite3.connect(tmp_path)
            cur = conn.cursor()

            # Create reference table
            cur.execute(f"""
                CREATE TABLE {ref_table} (
                    id   INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            for rr in ref_rows:
                cur.execute(
                    f"INSERT INTO {ref_table} (id, name) VALUES (?, ?)",
                    (rr["id"], rr["name"]),
                )

            # Create v1 main table (no FK constraint yet — added in migration)
            cur.execute(f"""
                CREATE TABLE {table} (
                    id           INTEGER PRIMARY KEY,
                    {old_label}  TEXT NOT NULL,
                    {old_contact} TEXT NOT NULL,
                    {old_state}  TEXT NOT NULL DEFAULT '{status_vals[0]}',
                    {old_value_col} {old_value_type} NOT NULL DEFAULT 0,
                    ref_id       INTEGER NOT NULL DEFAULT 1
                )
            """)
            for r in v1_rows:
                cur.execute(
                    f"INSERT INTO {table} "
                    f"(id, {old_label}, {old_contact}, {old_state}, {old_value_col}, ref_id) "
                    f"VALUES (?, ?, ?, ?, ?, ?)",
                    (r["id"], r[old_label], r[old_contact],
                     r[old_state], r[old_value_col], r["ref_id"]),
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
        ref_table: str,
        old_label: str, new_label: str,
        old_contact: str, new_contact: str,
        old_state: str, new_state: str,
        old_value_col: str, new_value_col: str,
        old_value_type: str, new_value_type: str,
        new_cols: list[tuple],
        indexes: list[dict],
    ) -> str:
        new_cols_repr = repr(new_cols)
        indexes_repr = repr(indexes)
        type_note = (
            f"  # NOTE: {old_value_col} ({old_value_type}) -> {new_value_col} ({new_value_type})"
            if old_value_type != new_value_type
            else f"  # NOTE: {old_value_col} stays {new_value_type} but is renamed to {new_value_col}"
        )
        return f'''"""
Database migration script: v1 -> v2 schema for table `{table}`.

Run with: python migration.py

Safe migration order (MUST follow to avoid data loss):
  1. Add new nullable columns to existing table
  2. Backfill / coerce data; rename columns via table-recreate trick
  3. Create indexes AFTER data has been moved
  4. Add FK constraint via table-recreate (SQLite requires full recreate)

Wrap all steps in a single transaction; roll back on any error.
Produce `migration_result.json` on success.
"""
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def migrate(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")  # must be OFF during table-recreate
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        # ── Step 1: Add new nullable columns ──────────────────────────────
        # New columns: {new_cols_repr}
        # TODO: ALTER TABLE {table} ADD COLUMN ...

        # ── Step 2: Recreate table with renamed columns + type change + FK ─
        # Column renames:
        #   {old_label}     -> {new_label}
        #   {old_contact}   -> {new_contact}
        #   {old_state}     -> {new_state}
        #   {old_value_col} -> {new_value_col}
{type_note}
        # FK: ref_id REFERENCES {ref_table}(id)
        # Strategy:
        #   a) CREATE TABLE {table}_new (new schema)
        #   b) INSERT INTO {table}_new SELECT (with casts) FROM {table}
        #   c) DROP TABLE {table}
        #   d) ALTER TABLE {table}_new RENAME TO {table}
        # TODO: implement table-recreate

        # ── Step 3: Create indexes ─────────────────────────────────────────
        # Indexes to create: {indexes_repr}
        # Example: cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_... ON {table}(...)")
        # IMPORTANT: create indexes AFTER data migration, not before.
        # TODO: create indexes

        # ── Step 4: Validate row count ────────────────────────────────────
        # TODO: SELECT COUNT(*) FROM {table} and assert it matches original count

        conn.commit()

    except Exception as exc:
        conn.rollback()
        print(f"Migration failed: {{exc}}")
        raise SystemExit(1) from exc
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

    # ── Write attestation ─────────────────────────────────────────────────
    result = {{
        "table": "{table}",
        "verdict": "pass",
    }}
    out_path = os.path.join(os.path.dirname(db_path), "migration_result.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
'''

    def _generate_spec(
        self,
        table: str,
        ref_table: str,
        old_label: str, new_label: str,
        old_contact: str, new_contact: str,
        old_state: str, new_state: str,
        old_value_col: str, new_value_col: str,
        old_value_type: str, new_value_type: str,
        new_cols: list[tuple],
        num_rows: int,
        status_vals: list[str],
        indexes: list[dict],
    ) -> str:
        status_vals_str = ", ".join(f'`"{v}"`' for v in status_vals)
        new_cols_sql = "\n".join(
            f"    {col}   {sql_type} NOT NULL DEFAULT {sql_dflt},"
            for col, sql_type, _py, sql_dflt in new_cols
        )
        new_cols_list = "\n".join(
            f"   - `{col}` {sql_type} — default: `{sql_dflt}`"
            for col, sql_type, _py, sql_dflt in new_cols
        )
        type_change_note = (
            f"  - `{old_value_col}` (`{old_value_type}`) → `{new_value_col}` (`{new_value_type}`): "
            f"cast integer cents to real (multiply by 1.0 or use `CAST(... AS REAL)`)"
            if old_value_type != new_value_type
            else f"  - `{old_value_col}` (`{old_value_type}`) → `{new_value_col}` (`{new_value_type}`): rename only, type unchanged"
        )
        indexes_md = "\n".join(
            f"   - `{'UNIQUE ' if idx['unique'] else ''}INDEX {idx['name']} ON {table}({idx['col']})`"
            for idx in indexes
        )

        return f"""# SPEC4: Database Schema Migration (Hard)

## Goal

Implement `migration.py` so it safely migrates `database.db` from v1 to v2
schema for the `{table}` table.  The reference table `{ref_table}` already
exists and must **not** be modified.

---

## v1 Schema (current state)

```sql
CREATE TABLE {ref_table} (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE {table} (
    id             INTEGER PRIMARY KEY,
    {old_label:<20} TEXT    NOT NULL,
    {old_contact:<20} TEXT    NOT NULL,
    {old_state:<20} TEXT    NOT NULL DEFAULT '{status_vals[0]}',
    {old_value_col:<20} {old_value_type:<7} NOT NULL DEFAULT 0,
    ref_id         INTEGER NOT NULL DEFAULT 1
);
```

The `{table}` table currently holds **{num_rows} rows**.
Status values in use: {status_vals_str}.

---

## v2 Schema (target state)

```sql
CREATE TABLE {table} (
    id             INTEGER PRIMARY KEY,
    {new_label:<20} TEXT    NOT NULL,
    {new_contact:<20} TEXT    NOT NULL UNIQUE,
    {new_state:<20} TEXT    NOT NULL DEFAULT '{status_vals[0]}',
    {new_value_col:<20} {new_value_type:<7} NOT NULL DEFAULT 0,
    ref_id         INTEGER NOT NULL
                           REFERENCES {ref_table}(id),
{new_cols_sql}
);
```

---

## Column Changes

### Renames
| v1 column | v2 column | Notes |
|-----------|-----------|-------|
| `{old_label}` | `{new_label}` | label rename |
| `{old_contact}` | `{new_contact}` | contact rename; gains UNIQUE constraint |
| `{old_state}` | `{new_state}` | state rename |
| `{old_value_col}` | `{new_value_col}` | value rename + possible type change |

### Type change
{type_change_note}

### New columns added (with defaults applied to all existing rows)
{new_cols_list}

---

## Migration Constraints

1. **Preserve all data**: every row in v1 must appear in v2 with the same `id`.
2. **Step order is mandatory** — wrong order causes data loss or constraint violations:
   - Step 1: Add new nullable columns (`ALTER TABLE ... ADD COLUMN`) so existing rows are unaffected.
   - Step 2: Recreate `{table}` with the full v2 schema (renames + type change + FK).
     Use the SQLite table-recreate pattern:
     ```
     CREATE TABLE {table}_new (v2 schema);
     INSERT INTO {table}_new SELECT id, {new_label}={old_label}, ..., CAST({old_value_col} AS {new_value_type}), ref_id, new_col1, ... FROM {table};
     DROP TABLE {table};
     ALTER TABLE {table}_new RENAME TO {table};
     ```
   - Step 3: Create indexes **after** data is in place (never before).
   - Step 4: Validate row count — raise and roll back if mismatch.
3. **Indexes to create after migration**:
{indexes_md}
4. **FK constraint**: `ref_id` must reference `{ref_table}(id)`.  Declare it in the new
   table DDL.  `PRAGMA foreign_keys` should be `OFF` during table-recreate, then `ON` after.
5. **Atomic transaction**: wrap all DDL/DML in `BEGIN` … `COMMIT`; `ROLLBACK` on any error.
6. **Idempotent**: running `migration.py` a second time must not crash or corrupt data.
7. **Run from workspace**: `python migration.py`

---

## Rollback Requirements

If any step raises an exception:
- Call `conn.rollback()` immediately.
- Print the error to stdout.
- Exit with code 1.
- The database must be left in a consistent state (v1 or v2, not partially migrated).

Recommended: backup the table as `{table}_backup` before the recreate step, drop it
after a successful commit.

---

## Deliverables

1. `migration.py` — complete, runnable migration script.
2. `migration_result.json` — written by the script on success:
   ```json
   {{
     "table": "{table}",
     "verdict": "pass"
   }}
   ```

---

## Acceptance Criteria (all must hold after running `python migration.py`)

- [ ] Script exits with code 0 and prints "Migration complete."
- [ ] `database.db` still exists.
- [ ] v2 column set is exact: old column names absent, new column names present.
- [ ] Row count equals {num_rows}.
- [ ] Data preserved: spot-checked rows have correct values under new column names.
- [ ] Value column type is `{new_value_type}`.
- [ ] All indexes from the index list above exist.
- [ ] `{new_contact}` has a UNIQUE constraint/index.
- [ ] `ref_id` FK references `{ref_table}(id)`.
- [ ] New columns have correct default values for pre-existing rows.
- [ ] Script is idempotent (second run does not raise).
- [ ] `migration_result.json` exists with `"verdict": "pass"`.
"""

    def _generate_brief(self, table: str) -> str:
        return f"""# SPEC4: Database Schema Migration

A database schema change is needed.  Write the migration script.

- **Workspace**: `database.db` (SQLite), `migration.py` (skeleton)
- **Run**: `python migration.py`
- **Success**: exits 0, prints "Migration complete.", writes `migration_result.json`

The Planner has the full spec with before/after schemas, step order, constraints,
and rollback requirements.
"""
