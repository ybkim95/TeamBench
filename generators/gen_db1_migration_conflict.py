"""
Parameterized generator for DB1: Database Migration Conflict Resolution.

Each seed produces a different application domain (e-commerce / social / analytics /
inventory / billing) with 3-4 conflicting SQL migrations arising from two feature
branches that were merged simultaneously.

Conflict types:
  C1. sequence_collision:   both branches add a migration with the same sequence number
  C2. column_rename_conflict: branch A renames a column, branch B adds a FK that
                               references the old column name
  C3. foreign_key_dep:      branch B's migration drops a table that branch A's later
                              migration still references via FK
  C4. index_name_collision: both branches create an index with the same name

Migration policy (in spec):
  - Branch order: feature/payments wins over feature/analytics on conflict
  - Merge order: apply baseline → feature/payments → feature/analytics
  - On sequence collision: feature/payments migration takes the lower sequence number

Information asymmetry (TNI pattern B):
  spec.md   — migration policy, conflict analysis, correct resolution order
  brief.md  — "resolve the migration conflicts" (no specifics)

Grade: apply resolved migrations to SQLite and check final schema matches expected.
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "ecommerce",
        "app": "ShopApp",
        "branch_a": "feature/payments",
        "branch_b": "feature/analytics",
        "primary_table": "orders",
        "secondary_table": "customers",
        "analytics_table": "order_metrics",
        "old_col": "customer_name",
        "new_col": "full_name",
        "fk_col": "customer_name",
        "amount_col": "total_amount",
        "status_col": "order_status",
        "extra_col": "region",
        "index_name": "idx_orders_customer",
        "baseline_tables": [
            ("customers", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "customer_name TEXT NOT NULL",
                "email TEXT UNIQUE NOT NULL",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]),
            ("orders", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "customer_id INTEGER NOT NULL",
                "total_amount DECIMAL(10,2) NOT NULL",
                "order_status TEXT DEFAULT 'pending'",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "FOREIGN KEY (customer_id) REFERENCES customers(id)",
            ]),
        ],
    },
    {
        "name": "social",
        "app": "SocialApp",
        "branch_a": "feature/messaging",
        "branch_b": "feature/recommendations",
        "primary_table": "posts",
        "secondary_table": "users",
        "analytics_table": "post_metrics",
        "old_col": "display_name",
        "new_col": "username",
        "fk_col": "display_name",
        "amount_col": "like_count",
        "status_col": "visibility",
        "extra_col": "language",
        "index_name": "idx_posts_user",
        "baseline_tables": [
            ("users", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "display_name TEXT NOT NULL",
                "email TEXT UNIQUE NOT NULL",
                "joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]),
            ("posts", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "user_id INTEGER NOT NULL",
                "content TEXT NOT NULL",
                "like_count INTEGER DEFAULT 0",
                "visibility TEXT DEFAULT 'public'",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "FOREIGN KEY (user_id) REFERENCES users(id)",
            ]),
        ],
    },
    {
        "name": "analytics",
        "app": "DataPlatform",
        "branch_a": "feature/ingestion",
        "branch_b": "feature/reporting",
        "primary_table": "events",
        "secondary_table": "sources",
        "analytics_table": "event_aggregates",
        "old_col": "source_name",
        "new_col": "source_label",
        "fk_col": "source_name",
        "amount_col": "event_count",
        "status_col": "processing_status",
        "extra_col": "environment",
        "index_name": "idx_events_source",
        "baseline_tables": [
            ("sources", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "source_name TEXT NOT NULL",
                "source_type TEXT NOT NULL",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]),
            ("events", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "source_id INTEGER NOT NULL",
                "event_type TEXT NOT NULL",
                "event_count INTEGER DEFAULT 0",
                "processing_status TEXT DEFAULT 'pending'",
                "occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "FOREIGN KEY (source_id) REFERENCES sources(id)",
            ]),
        ],
    },
    {
        "name": "inventory",
        "app": "WarehouseApp",
        "branch_a": "feature/receiving",
        "branch_b": "feature/forecasting",
        "primary_table": "items",
        "secondary_table": "warehouses",
        "analytics_table": "stock_metrics",
        "old_col": "warehouse_name",
        "new_col": "location_name",
        "fk_col": "warehouse_name",
        "amount_col": "quantity",
        "status_col": "item_status",
        "extra_col": "zone",
        "index_name": "idx_items_warehouse",
        "baseline_tables": [
            ("warehouses", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "warehouse_name TEXT NOT NULL",
                "capacity INTEGER NOT NULL",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]),
            ("items", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "warehouse_id INTEGER NOT NULL",
                "sku TEXT NOT NULL",
                "quantity INTEGER DEFAULT 0",
                "item_status TEXT DEFAULT 'available'",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)",
            ]),
        ],
    },
    {
        "name": "billing",
        "app": "BillingService",
        "branch_a": "feature/subscriptions",
        "branch_b": "feature/usage-tracking",
        "primary_table": "invoices",
        "secondary_table": "accounts",
        "analytics_table": "billing_metrics",
        "old_col": "account_name",
        "new_col": "company_name",
        "fk_col": "account_name",
        "amount_col": "amount_due",
        "status_col": "invoice_status",
        "extra_col": "currency",
        "index_name": "idx_invoices_account",
        "baseline_tables": [
            ("accounts", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "account_name TEXT NOT NULL",
                "email TEXT UNIQUE NOT NULL",
                "plan TEXT DEFAULT 'free'",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]),
            ("invoices", [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "account_id INTEGER NOT NULL",
                "amount_due DECIMAL(10,2) NOT NULL",
                "invoice_status TEXT DEFAULT 'draft'",
                "due_date DATE",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "FOREIGN KEY (account_id) REFERENCES accounts(id)",
            ]),
        ],
    },
]

# Which conflict types appear per seed
CONFLICT_SETS = [
    ["sequence_collision", "column_rename_conflict", "foreign_key_dep", "index_name_collision"],
    ["sequence_collision", "column_rename_conflict", "foreign_key_dep"],
    ["sequence_collision", "column_rename_conflict", "index_name_collision"],
    ["sequence_collision", "foreign_key_dep", "index_name_collision"],
    ["column_rename_conflict", "foreign_key_dep", "index_name_collision"],
]


class Generator(TaskGenerator):
    task_id = "DB1_migration_conflict"
    domain = "Data Engineering"
    difficulty = "hard"
    languages = ["sql", "python"]

    @staticmethod
    def _clean(s: str) -> str:
        """Strip common leading whitespace from every line (handles f-string indent issues)."""
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        conflict_idx = seed % len(CONFLICT_SETS)
        cfg = DOMAINS[domain_idx]
        conflicts = CONFLICT_SETS[conflict_idx]

        # Seed-parameterized values
        seq_base = rng.randint(3, 7)  # starting sequence number for conflict area
        extra_col_default = rng.choice(["'default'", "'unknown'", "'N/A'", "NULL"])

        workspace_files = self._make_workspace(cfg, conflicts, seq_base, extra_col_default)
        spec_md = self._clean(self._make_spec(cfg, conflicts, seq_base, extra_col_default))
        brief_md = self._clean(self._make_brief(cfg))

        # Compute expected final schema columns
        expected_secondary_cols = self._expected_secondary_cols(cfg, conflicts)
        expected_primary_cols = self._expected_primary_cols(cfg, conflicts, extra_col_default)
        expected_analytics_table = self._has_analytics_table(cfg, conflicts)

        return GeneratedTask(
            task_id="DB1_migration_conflict",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "branch_a": cfg["branch_a"],
                "branch_b": cfg["branch_b"],
                "conflicts": conflicts,
                "seq_base": seq_base,
                "primary_table": cfg["primary_table"],
                "secondary_table": cfg["secondary_table"],
                "analytics_table": cfg["analytics_table"],
                "expected_secondary_cols": expected_secondary_cols,
                "expected_primary_cols": expected_primary_cols,
                "analytics_table_exists": expected_analytics_table,
                "final_migration_order": self._migration_order(cfg, conflicts, seq_base),
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "Data Engineering"},
        )

    # ── Schema helpers ─────────────────────────────────────────────────────────

    def _expected_secondary_cols(self, cfg: dict, conflicts: list) -> list:
        """Columns in the secondary table after correct resolution."""
        # Start with baseline cols
        cols = ["id", cfg["old_col"], "email", "created_at"]
        if "column_rename_conflict" in conflicts:
            # Branch A renames old_col -> new_col (wins)
            cols = [c if c != cfg["old_col"] else cfg["new_col"] for c in cols]
        return cols

    def _expected_primary_cols(self, cfg: dict, conflicts: list, extra_col_default: str) -> list:
        """Columns in the primary table after correct resolution."""
        # baseline cols
        baseline = [c.split()[0] for t, cols in cfg["baseline_tables"]
                    if t == cfg["primary_table"] for c in cols
                    if not c.startswith("FOREIGN")]
        cols = list(baseline)
        if cfg["extra_col"] not in cols:
            cols.append(cfg["extra_col"])
        return cols

    def _has_analytics_table(self, cfg: dict, conflicts: list) -> bool:
        """Analytics table is created by branch B (always present after correct resolution)."""
        return "foreign_key_dep" not in conflicts or True  # analytics table always survives

    def _migration_order(self, cfg: dict, conflicts: list, seq_base: int) -> list:
        """Correct resolved migration filenames in application order."""
        order = [
            f"0001_baseline.sql",
            f"000{seq_base}_branch_a_rename_col.sql",
            f"000{seq_base + 1}_branch_b_add_analytics.sql",
        ]
        if "index_name_collision" in conflicts:
            order.append(f"000{seq_base + 2}_branch_a_add_index.sql")
        return order

    # ── Workspace file generators ──────────────────────────────────────────────

    def _make_workspace(
        self, cfg: dict, conflicts: list, seq_base: int, extra_col_default: str
    ) -> dict:
        files = {}

        # Baseline migration (always correct)
        files["migrations/0001_baseline.sql"] = self._make_baseline(cfg)

        # Conflicting migrations from two branches
        files[f"migrations/000{seq_base}_branch_a_rename_col.sql"] = \
            self._make_branch_a_migration(cfg, conflicts, seq_base, extra_col_default)
        files[f"migrations/000{seq_base}_branch_b_add_analytics.sql"] = \
            self._make_branch_b_migration_conflicting(cfg, conflicts, seq_base)
        files[f"migrations/000{seq_base + 1}_branch_b_add_analytics.sql"] = \
            self._make_branch_b_migration(cfg, conflicts, seq_base)

        if "index_name_collision" in conflicts:
            files[f"migrations/000{seq_base + 2}_branch_a_add_index.sql"] = \
                self._make_index_migration_a(cfg, seq_base)
            files[f"migrations/000{seq_base + 2}_branch_b_add_index.sql"] = \
                self._make_index_migration_b(cfg, seq_base)

        files["migration_policy.md"] = self._make_policy(cfg, conflicts, seq_base)
        files["apply_migrations.py"] = self._make_apply_script(cfg, conflicts, seq_base)
        files["verify_schema.py"] = self._make_verify_script(cfg, conflicts, extra_col_default)

        return files

    def _make_baseline(self, cfg: dict) -> str:
        lines = ["-- 0001_baseline.sql: Initial schema", ""]
        for table, cols in cfg["baseline_tables"]:
            col_block = ",\n    ".join(cols)
            lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
            lines.append(f"    {col_block}")
            lines.append(");")
            lines.append("")
        return "\n".join(lines)

    def _make_branch_a_migration(
        self, cfg: dict, conflicts: list, seq_base: int, extra_col_default: str
    ) -> str:
        branch = cfg["branch_a"]
        primary = cfg["primary_table"]
        secondary = cfg["secondary_table"]
        old_col = cfg["old_col"]
        new_col = cfg["new_col"]
        extra_col = cfg["extra_col"]

        lines = [
            f"-- 000{seq_base}_branch_a_rename_col.sql",
            f"-- Branch: {branch}",
            f"-- Purpose: Rename {old_col} -> {new_col} in {secondary}; add {extra_col} to {primary}",
            "",
        ]

        if "column_rename_conflict" in conflicts:
            # SQLite workaround for RENAME COLUMN: recreate the table
            lines += [
                f"-- Rename {old_col} to {new_col} in {secondary}",
                f"-- SQLite workaround: recreate table",
                f"ALTER TABLE {secondary} RENAME TO {secondary}_old;",
                "",
                f"CREATE TABLE {secondary} (",
            ]
            # Collect column definitions (excluding FOREIGN KEY constraints)
            new_col_defs = []
            for table, cols in cfg["baseline_tables"]:
                if table == secondary:
                    for col in cols:
                        if col.startswith("FOREIGN"):
                            continue
                        if col.startswith(old_col):
                            new_col_defs.append("    " + col.replace(old_col, new_col, 1))
                        else:
                            new_col_defs.append("    " + col)
            # Join with commas, no trailing comma
            lines.append(",\n".join(new_col_defs))
            lines.append(");")
            lines.append("")
            # Build SELECT column list from the baseline — use old col name in source
            select_cols = []
            for table, cols in cfg["baseline_tables"]:
                if table == secondary:
                    for col in cols:
                        if col.startswith("FOREIGN"):
                            continue
                        col_name = col.split()[0]
                        select_cols.append(col_name)  # old column names in _old table
            select_list = ", ".join(select_cols)
            lines.append(f"INSERT INTO {secondary} SELECT {select_list} FROM {secondary}_old;")
            lines.append(f"DROP TABLE {secondary}_old;")
        else:
            lines += [
                f"-- No column rename in this seed",
            ]

        lines += [
            "",
            f"-- Add {extra_col} column to {primary}",
            f"ALTER TABLE {primary} ADD COLUMN {extra_col} TEXT DEFAULT {extra_col_default};",
        ]

        return "\n".join(lines) + "\n"

    def _make_branch_b_migration_conflicting(
        self, cfg: dict, conflicts: list, seq_base: int
    ) -> str:
        """The conflicting version of branch B's migration (same sequence number as branch A)."""
        branch = cfg["branch_b"]
        analytics = cfg["analytics_table"]
        primary = cfg["primary_table"]
        amount_col = cfg["amount_col"]
        old_col = cfg["old_col"]  # uses old name — conflict with rename

        lines = [
            f"-- 000{seq_base}_branch_b_add_analytics.sql  *** CONFLICT: same sequence as branch A ***",
            f"-- Branch: {branch}",
            f"-- WARNING: This file has a sequence collision with branch A's migration.",
            f"-- It also references the OLD column name '{old_col}' which branch A renames.",
            f"-- This file must be RENAMED and FIXED before applying.",
            "",
        ]

        if "sequence_collision" in conflicts:
            lines += [
                f"-- CONFLICT C1: sequence number 000{seq_base} is already used by {cfg['branch_a']}.",
                f"-- Resolution: rename this file to 000{seq_base + 1}_branch_b_add_analytics.sql",
                "",
            ]

        if "column_rename_conflict" in conflicts:
            lines += [
                f"-- CONFLICT C2: this migration references {old_col} which branch A renames to {cfg['new_col']}.",
                f"-- After applying branch A's rename, this reference will fail.",
                f"-- Resolution (in the renamed file): update reference to use {cfg['new_col']}",
                "",
            ]

        lines += [
            f"CREATE TABLE IF NOT EXISTS {analytics} (",
            f"    id INTEGER PRIMARY KEY AUTOINCREMENT,",
            f"    {primary[:-1]}_id INTEGER NOT NULL,",
            f"    {old_col} TEXT,  -- CONFLICT: should be {cfg['new_col']} after branch A rename",
            f"    total_{amount_col} DECIMAL(12,2) DEFAULT 0,",
            f"    period DATE NOT NULL,",
            f"    FOREIGN KEY ({primary[:-1]}_id) REFERENCES {primary}(id)",
            f");",
        ]

        return "\n".join(lines) + "\n"

    def _make_branch_b_migration(
        self, cfg: dict, conflicts: list, seq_base: int
    ) -> str:
        """The corrected branch B migration (sequence + column name fixed)."""
        branch = cfg["branch_b"]
        analytics = cfg["analytics_table"]
        primary = cfg["primary_table"]
        amount_col = cfg["amount_col"]
        new_col = cfg["new_col"]

        lines = [
            f"-- 000{seq_base + 1}_branch_b_add_analytics.sql",
            f"-- Branch: {branch} (RESOLVED: renamed from 000{seq_base} + column ref updated)",
            f"-- Purpose: Add analytics metrics table",
            "",
            f"CREATE TABLE IF NOT EXISTS {analytics} (",
            f"    id INTEGER PRIMARY KEY AUTOINCREMENT,",
            f"    {primary[:-1]}_id INTEGER NOT NULL,",
            f"    {new_col} TEXT,  -- RESOLVED: using new column name after branch A rename",
            f"    total_{amount_col} DECIMAL(12,2) DEFAULT 0,",
            f"    period DATE NOT NULL,",
            f"    FOREIGN KEY ({primary[:-1]}_id) REFERENCES {primary}(id)",
            f");",
        ]

        return "\n".join(lines) + "\n"

    def _make_index_migration_a(self, cfg: dict, seq_base: int) -> str:
        primary = cfg["primary_table"]
        index_name = cfg["index_name"]
        amount_col = cfg["amount_col"]

        return textwrap.dedent(f"""\
            -- 000{seq_base + 2}_branch_a_add_index.sql
            -- Branch: {cfg['branch_a']}
            -- CONFLICT C4: index name '{index_name}' also used by branch B
            -- Resolution: this file wins (branch A takes precedence)
            -- Branch B's index file (000{seq_base + 2}_branch_b_add_index.sql) must be DELETED

            CREATE INDEX IF NOT EXISTS {index_name}
                ON {primary} ({amount_col});
            """)

    def _make_index_migration_b(self, cfg: dict, seq_base: int) -> str:
        primary = cfg["primary_table"]
        index_name = cfg["index_name"]
        status_col = cfg["status_col"]

        return textwrap.dedent(f"""\
            -- 000{seq_base + 2}_branch_b_add_index.sql
            -- Branch: {cfg['branch_b']}
            -- CONFLICT C4: index name '{index_name}' also used by branch A
            -- This file must be DELETED — branch A's index takes precedence per migration policy
            -- If a separate index on {status_col} is needed, use a different name.

            CREATE INDEX IF NOT EXISTS {index_name}
                ON {primary} ({status_col});
            """)

    def _make_policy(self, cfg: dict, conflicts: list, seq_base: int) -> str:
        return textwrap.dedent(f"""\
            # Migration Policy — {cfg['app']}

            ## Branch Priority

            When two feature branches produce conflicting migrations, the following
            priority order applies:

            1. **`{cfg['branch_a']}`** — highest priority (wins all conflicts)
            2. **`{cfg['branch_b']}`** — lower priority (must be adapted to not conflict)

            ## Merge Order

            Apply migrations in this sequence:
            1. Baseline migrations (`0001_baseline.sql`)
            2. `{cfg['branch_a']}` migrations (in sequence number order)
            3. `{cfg['branch_b']}` migrations (in sequence number order, after renaming)

            ## Conflict Resolution Rules

            ### Sequence Number Collisions

            If two migrations have the same sequence number, the lower-priority branch's
            migration must be **renumbered** to the next available sequence number.
            The higher-priority branch's file keeps its original number.

            ### Column Name Conflicts

            If branch A renames a column and branch B references the old column name,
            branch B's migration must be updated to use the new column name.
            Apply branch A's migration first.

            ### Index Name Collisions

            If two branches create an index with the same name, the higher-priority
            branch's index file is kept unchanged. The lower-priority branch's index
            file must be **deleted** (the index is considered covered by the winning branch).

            ## Expected Final State

            After applying all resolved migrations, the database should contain:
            - `{cfg['secondary_table']}` with column `{cfg['new_col']}` (renamed from `{cfg['old_col']}`)
            - `{cfg['primary_table']}` with an added `{cfg['extra_col']}` column
            - `{cfg['analytics_table']}` referencing the new column name `{cfg['new_col']}`
            - Index `{cfg['index_name']}` created by `{cfg['branch_a']}`
            """)

    def _make_apply_script(self, cfg: dict, conflicts: list, seq_base: int) -> str:
        return textwrap.dedent(f"""\
            #!/usr/bin/env python3
            \"\"\"
            apply_migrations.py — Apply resolved migrations to a SQLite database.

            Usage:
                python apply_migrations.py [db_path]

            The script applies all .sql files in the migrations/ directory in
            lexicographic order. Conflicting/duplicate files must be resolved
            before running this script.
            \"\"\"
            import sqlite3
            import os
            import sys
            import glob

            DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "schema.db"
            MIGRATIONS_DIR = "migrations"


            def apply_migrations(db_path: str) -> None:
                conn = sqlite3.connect(db_path)
                conn.execute("PRAGMA foreign_keys = ON")

                migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))

                if not migration_files:
                    print(f"No migration files found in {{MIGRATIONS_DIR}}/")
                    return

                applied = 0
                for migration_file in migration_files:
                    print(f"Applying: {{migration_file}}")
                    with open(migration_file) as f:
                        sql = f.read()
                    try:
                        conn.executescript(sql)
                        applied += 1
                    except sqlite3.Error as e:
                        print(f"  ERROR: {{e}}")
                        conn.close()
                        sys.exit(1)

                conn.commit()
                conn.close()
                print(f"\\nApplied {{applied}} migration(s) to {{db_path}}")


            if __name__ == "__main__":
                apply_migrations(DB_PATH)
            """)

    def _make_verify_script(
        self, cfg: dict, conflicts: list, extra_col_default: str
    ) -> str:
        primary = cfg["primary_table"]
        secondary = cfg["secondary_table"]
        analytics = cfg["analytics_table"]
        new_col = cfg["new_col"]
        old_col = cfg["old_col"]
        extra_col = cfg["extra_col"]
        index_name = cfg["index_name"]
        has_index_conflict = "index_name_collision" in conflicts
        has_rename_conflict = "column_rename_conflict" in conflicts

        return textwrap.dedent(f"""\
            #!/usr/bin/env python3
            \"\"\"
            verify_schema.py — Verify the resolved migration produces the expected schema.

            Usage:
                python apply_migrations.py schema.db && python verify_schema.py schema.db
            \"\"\"
            import sqlite3
            import sys

            DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "schema.db"

            checks_passed = 0
            checks_total = 0
            failures = []


            def check(description: str, result: bool) -> None:
                global checks_passed, checks_total
                checks_total += 1
                status = "PASS" if result else "FAIL"
                print(f"  [{{status}}] {{description}}")
                if result:
                    checks_passed += 1
                else:
                    failures.append(description)


            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row


            def get_columns(table: str) -> list:
                rows = conn.execute(f"PRAGMA table_info({{table}})").fetchall()
                return [r["name"] for r in rows]


            def table_exists(table: str) -> bool:
                r = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                ).fetchone()
                return r is not None


            def index_exists(index: str) -> bool:
                r = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (index,)
                ).fetchone()
                return r is not None


            print(f"Verifying schema in {{DB_PATH}}...")
            print()

            # C1: Secondary table has new column name
            cols = get_columns("{secondary}")
            check(
                f"'{secondary}' has column '{new_col}' (renamed from '{old_col}')",
                "{new_col}" in cols
            )
            check(
                f"'{secondary}' does NOT have old column '{old_col}'",
                "{old_col}" not in cols
            )

            # C2: Primary table has extra column
            cols = get_columns("{primary}")
            check(
                f"'{primary}' has new column '{extra_col}'",
                "{extra_col}" in cols
            )

            # C3: Analytics table exists with correct column reference
            check(
                f"Analytics table '{analytics}' exists",
                table_exists("{analytics}")
            )
            if table_exists("{analytics}"):
                analytics_cols = get_columns("{analytics}")
                check(
                    f"'{analytics}' references '{new_col}' (not old '{old_col}')",
                    "{new_col}" in analytics_cols and "{old_col}" not in analytics_cols
                )
            else:
                checks_total += 1  # count the skipped sub-check
                failures.append(f"'{analytics}' column check skipped — table missing")

            # C4: No duplicate migration files (check by counting SQL files)
            import glob, os
            sql_files = glob.glob("migrations/*.sql")
            seq_nums = [os.path.basename(f).split("_")[0] for f in sql_files]
            has_duplicates = len(seq_nums) != len(set(seq_nums))
            check(
                "No duplicate sequence numbers in migrations/",
                not has_duplicates
            )

            # C5: Index exists (only checked when index conflict was present)
            if {has_index_conflict}:
                check(
                    f"Index '{index_name}' exists",
                    index_exists("{index_name}")
                )

            conn.close()

            print()
            print(f"Result: {{checks_passed}}/{{checks_total}} checks passed")
            if failures:
                print("Failed checks:")
                for f in failures:
                    print(f"  - {{f}}")
                sys.exit(1)
            else:
                print("All checks passed!")
            """)

    # ── Spec / Brief generators ────────────────────────────────────────────────

    def _make_spec(
        self, cfg: dict, conflicts: list, seq_base: int, extra_col_default: str
    ) -> str:
        branch_a = cfg["branch_a"]
        branch_b = cfg["branch_b"]
        primary = cfg["primary_table"]
        secondary = cfg["secondary_table"]
        analytics = cfg["analytics_table"]
        old_col = cfg["old_col"]
        new_col = cfg["new_col"]
        extra_col = cfg["extra_col"]
        index_name = cfg["index_name"]
        amount_col = cfg["amount_col"]

        conflict_rows = []
        if "sequence_collision" in conflicts:
            conflict_rows.append(
                f"| C1 | sequence_collision | Both branches use `000{seq_base}_*.sql` | "
                f"Rename `{branch_b}`'s file to `000{seq_base + 1}_branch_b_add_analytics.sql` |"
            )
        if "column_rename_conflict" in conflicts:
            conflict_rows.append(
                f"| C2 | column_rename_conflict | `{branch_b}` references `{old_col}` after `{branch_a}` renames it | "
                f"Update `{analytics}` DDL to use `{new_col}` |"
            )
        if "foreign_key_dep" in conflicts:
            conflict_rows.append(
                f"| C3 | foreign_key_dep | Analytics table FK would reference stale column name | "
                f"Apply `{branch_a}` rename before `{branch_b}` analytics table |"
            )
        if "index_name_collision" in conflicts:
            conflict_rows.append(
                f"| C4 | index_name_collision | Both branches create index `{index_name}` | "
                f"Delete `{branch_b}`'s index file; keep `{branch_a}`'s |"
            )

        conflict_table = "\n".join(conflict_rows)

        return textwrap.dedent(f"""\
            # DB1_migration_conflict: Migration Conflict Resolution — Full Specification (Planner Only)

            ## Overview

            Two feature branches (`{branch_a}` and `{branch_b}`) were developed in
            parallel for the `{cfg['app']}` {cfg['name']} application. Both branches
            produced SQL migrations that conflict with each other. The executor must
            resolve the conflicts so the migrations can be applied cleanly to produce
            the correct final schema.

            There are **{len(conflicts)} conflicts** to resolve. The executor only receives
            the brief; this spec provides the full analysis.

            ## File Structure

            ```
            migrations/
              0001_baseline.sql                              ← correct, do not modify
              000{seq_base}_branch_a_rename_col.sql          ← from {branch_a} (wins on conflict)
              000{seq_base}_branch_b_add_analytics.sql       ← CONFLICT: same seq# as branch A
              000{seq_base + 1}_branch_b_add_analytics.sql   ← resolved version (already present)
            {"  000" + str(seq_base + 2) + "_branch_a_add_index.sql            ← branch A index (keep)" if "index_name_collision" in conflicts else ""}
            {"  000" + str(seq_base + 2) + "_branch_b_add_index.sql            ← CONFLICT: duplicate index (delete)" if "index_name_collision" in conflicts else ""}
            migration_policy.md                             ← authoritative conflict resolution rules
            apply_migrations.py                             ← helper to apply migrations to SQLite
            verify_schema.py                                ← schema verification script
            ```

            ## Migration Policy

            - **Branch priority:** `{branch_a}` > `{branch_b}`
            - **Merge order:** baseline → `{branch_a}` migrations → `{branch_b}` migrations
            - **On sequence collision:** the lower-priority branch's file is renumbered
            - **On column reference conflict:** update to use the name from the higher-priority branch
            - **On index name collision:** keep the higher-priority branch's index; delete the other

            ## Conflict Analysis

            | # | Type | Problem | Resolution |
            |---|------|---------|------------|
            {conflict_table}

            ### Conflict Details

            """) + self._spec_conflict_details(cfg, conflicts, seq_base, extra_col_default) + textwrap.dedent(f"""\

            ## Expected Final Schema

            After applying all resolved migrations, the database must have:

            ### `{secondary}` table
            - Column `{new_col}` (renamed from `{old_col}`) — **not** `{old_col}`
            - All other baseline columns unchanged

            ### `{primary}` table
            - All baseline columns present
            - New column `{extra_col}` (added by `{branch_a}`)

            ### `{analytics}` table
            - Column `{new_col}` (not `{old_col}`)
            - FK reference to `{primary}`

            ### Indexes
            - `{index_name}` exists (from `{branch_a}`)

            ## Acceptance Criteria

            1. No two migration files have the same sequence number prefix
            2. `python apply_migrations.py schema.db` completes without errors
            3. `python verify_schema.py schema.db` reports all checks passed
            4. `{secondary}.{new_col}` exists; `{secondary}.{old_col}` does not
            5. `{primary}.{extra_col}` exists
            6. `{analytics}` table references `{new_col}` not `{old_col}`
            """)

    def _spec_conflict_details(
        self, cfg: dict, conflicts: list, seq_base: int, extra_col_default: str
    ) -> str:
        branch_a = cfg["branch_a"]
        branch_b = cfg["branch_b"]
        old_col = cfg["old_col"]
        new_col = cfg["new_col"]
        analytics = cfg["analytics_table"]
        index_name = cfg["index_name"]
        primary = cfg["primary_table"]

        sections = []

        if "sequence_collision" in conflicts:
            sections.append(textwrap.dedent(f"""\
                ### Conflict C1 — Sequence Number Collision

                **Files:** `000{seq_base}_branch_a_rename_col.sql` and
                `000{seq_base}_branch_b_add_analytics.sql`

                **Root cause:** Both branches were cut from the same baseline and
                independently chose sequence number `000{seq_base}`. Applying both
                in the same database will fail because the migration runner processes
                them in lexicographic order and can't determine which is authoritative.

                **Resolution:** Per policy, `{branch_a}` wins. The `{branch_b}` file
                `000{seq_base}_branch_b_add_analytics.sql` must be **renamed** to
                `000{seq_base + 1}_branch_b_add_analytics.sql`.

                The corrected file is already present as
                `000{seq_base + 1}_branch_b_add_analytics.sql` — delete the conflicting
                `000{seq_base}_branch_b_add_analytics.sql`.
                """))

        if "column_rename_conflict" in conflicts:
            sections.append(textwrap.dedent(f"""\
                ### Conflict C2 — Column Rename Reference Conflict

                **Files:** `000{seq_base}_branch_a_rename_col.sql` renames `{old_col}` → `{new_col}`.
                `000{seq_base}_branch_b_add_analytics.sql` creates `{analytics}` with
                a column called `{old_col}` (the stale name).

                **Root cause:** Branch B was developed against the old schema and still
                references `{old_col}`. After branch A's rename is applied, `{old_col}`
                no longer exists as a column in the secondary table. Branch B's analytics
                table uses the old name inconsistently.

                **Resolution:** The corrected file (`000{seq_base + 1}_branch_b_add_analytics.sql`)
                already uses `{new_col}`. Delete the conflicting original.
                """))

        if "foreign_key_dep" in conflicts:
            sections.append(textwrap.dedent(f"""\
                ### Conflict C3 — Foreign Key Dependency Order

                **Issue:** The analytics table must be created **after** the column rename
                is complete. If `{branch_b}`'s migration runs before `{branch_a}`'s rename,
                the FK reference will point to a non-existent column name.

                **Resolution:** Ensure `{branch_a}` migrations are fully applied before
                `{branch_b}` migrations. This is already satisfied by the sequence numbering
                after resolving C1 — `000{seq_base}` (branch A) runs before `000{seq_base + 1}` (branch B).
                """))

        if "index_name_collision" in conflicts:
            sections.append(textwrap.dedent(f"""\
                ### Conflict C4 — Index Name Collision

                **Files:** `000{seq_base + 2}_branch_a_add_index.sql` and
                `000{seq_base + 2}_branch_b_add_index.sql` both create an index
                named `{index_name}`.

                **Root cause:** Both branches independently chose the same index name.
                Applying both would fail with "index already exists".

                **Resolution:** Per policy, `{branch_a}` wins. Delete
                `000{seq_base + 2}_branch_b_add_index.sql`.
                Keep `000{seq_base + 2}_branch_a_add_index.sql`.
                """))

        return "\n".join(sections)

    def _make_brief(self, cfg: dict) -> str:
        branch_a = cfg["branch_a"]
        branch_b = cfg["branch_b"]
        primary = cfg["primary_table"]
        secondary = cfg["secondary_table"]

        return textwrap.dedent(f"""\
            # DB1_migration_conflict (Brief)

            Two feature branches (`{branch_a}` and `{branch_b}`) produced conflicting
            SQL migrations for the `{cfg['app']}` database. Resolve the conflicts so
            all migrations apply cleanly and the final schema is correct.

            ```bash
            python apply_migrations.py schema.db
            python verify_schema.py schema.db
            ```

            Both commands must complete without errors.

            **Files to work in:** `migrations/`
            **Reference:** `migration_policy.md` describes the conflict resolution rules.
            **Do NOT modify:** `0001_baseline.sql`, `apply_migrations.py`, `verify_schema.py`

            Follow the Planner's guidance precisely.
            """)
