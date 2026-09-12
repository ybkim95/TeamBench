"""
Parameterized generator for DB2_query_regression.

Schema change has caused query performance regressions. Some queries need
indexes (genuine bottlenecks on large tables), others must NOT get indexes
(small lookup tables where a sequential scan is faster, documented in DBA
analysis).

Information asymmetry (TNI pattern B):
  spec.md   — DBA EXPLAIN analysis identifying which queries are genuine
               regressions vs acceptable, plus exact index DDL to add
  brief.md  — "optimize the slow queries" (no specifics)

Each seed produces a different domain (ecommerce / social / analytics /
inventory / billing) with:

  Genuine bottlenecks (3-4 queries, need indexes):
    Q1. large table full scan — orders/posts/events/items/invoices (millions of rows)
    Q2. join missing index on FK column after schema change
    Q3. range query on timestamp column (no index)
    Q4. composite query on 2 columns (sometimes present, seed-dependent)

  Acceptable seq scans (2 queries, must NOT get indexes):
    S1. small reference/config table (< 1000 rows) — seq scan is faster
    S2. stats/summary table queried infrequently with full aggregation

Grade checks (static — parse SQL files, check index definitions):
  C1  schema.sql present in workspace
  C2  queries.sql present in workspace
  C3  dba_analysis.md present in workspace
  C4  indexes.sql present (agent must create this file)
  C5  Q1 index exists (large table, FK/filter column)
  C6  Q2 index exists (FK join column)
  C7  Q3 index exists (timestamp range column)
  C8  Q4 index exists (composite, if applicable to this seed)
  C9  S1 small table NOT indexed (no CREATE INDEX on small table)
  C10 S2 summary table NOT indexed (no CREATE INDEX on summary table)
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "ecommerce",
        "language": "SQL",
        "description": "e-commerce order management system",
        # Large tables needing indexes
        "large_table": "orders",
        "large_table_rows": "12 million",
        "large_table_filter_col": "customer_id",
        "large_table_filter_type": "INT NOT NULL",
        "join_table": "order_items",
        "join_table_rows": "45 million",
        "join_fk_col": "order_id",
        "join_fk_type": "INT NOT NULL",
        "ts_table": "order_events",
        "ts_table_rows": "8 million",
        "ts_col": "event_at",
        "ts_col_type": "TIMESTAMP NOT NULL",
        "composite_table": "products",
        "composite_table_rows": "2 million",
        "composite_col1": "category_id",
        "composite_col2": "status",
        "composite_col1_type": "INT NOT NULL",
        "composite_col2_type": "VARCHAR(20) NOT NULL",
        # Small tables — do NOT index
        "small_table": "payment_methods",
        "small_table_rows": "12",
        "small_table_desc": "payment method reference (12 rows)",
        "small_filter_col": "code",
        "summary_table": "daily_order_summary",
        "summary_table_rows": "365",
        "summary_table_desc": "daily aggregated totals (365 rows)",
        "summary_col": "summary_date",
        # Schema change context
        "schema_change": "orders table had customer_id added as a column after splitting from a legacy users table; the new FK column has no index",
        "product_name": "OrderTrack Pro",
    },
    {
        "name": "social",
        "language": "SQL",
        "description": "social media platform",
        "large_table": "posts",
        "large_table_rows": "50 million",
        "large_table_filter_col": "user_id",
        "large_table_filter_type": "BIGINT NOT NULL",
        "join_table": "post_likes",
        "join_table_rows": "200 million",
        "join_fk_col": "post_id",
        "join_fk_type": "BIGINT NOT NULL",
        "ts_table": "user_sessions",
        "ts_table_rows": "15 million",
        "ts_col": "started_at",
        "ts_col_type": "TIMESTAMP NOT NULL",
        "composite_table": "notifications",
        "composite_table_rows": "30 million",
        "composite_col1": "recipient_id",
        "composite_col2": "read_status",
        "composite_col1_type": "BIGINT NOT NULL",
        "composite_col2_type": "BOOLEAN NOT NULL",
        "small_table": "content_types",
        "small_table_rows": "8",
        "small_table_desc": "content type reference (8 rows)",
        "small_filter_col": "type_code",
        "summary_table": "weekly_engagement_summary",
        "summary_table_rows": "52",
        "summary_table_desc": "weekly engagement aggregates (52 rows)",
        "summary_col": "week_start",
        "schema_change": "posts table had user_id column added after denormalizing from a joined users query; the new column has no index",
        "product_name": "SocialGraph",
    },
    {
        "name": "analytics",
        "language": "SQL",
        "description": "product analytics pipeline",
        "large_table": "events",
        "large_table_rows": "500 million",
        "large_table_filter_col": "session_id",
        "large_table_filter_type": "VARCHAR(64) NOT NULL",
        "join_table": "event_properties",
        "join_table_rows": "1 billion",
        "join_fk_col": "event_id",
        "join_fk_type": "BIGINT NOT NULL",
        "ts_table": "pageviews",
        "ts_table_rows": "100 million",
        "ts_col": "viewed_at",
        "ts_col_type": "TIMESTAMP NOT NULL",
        "composite_table": "funnels",
        "composite_table_rows": "5 million",
        "composite_col1": "project_id",
        "composite_col2": "funnel_step",
        "composite_col1_type": "INT NOT NULL",
        "composite_col2_type": "INT NOT NULL",
        "small_table": "event_types",
        "small_table_rows": "24",
        "small_table_desc": "event type catalog (24 rows)",
        "small_filter_col": "type_name",
        "summary_table": "monthly_retention_summary",
        "summary_table_rows": "36",
        "summary_table_desc": "monthly retention cohort summary (36 rows)",
        "summary_col": "cohort_month",
        "schema_change": "events table had session_id column added during a refactor to track anonymous sessions; the new column has no index",
        "product_name": "DataPulse Analytics",
    },
    {
        "name": "inventory",
        "language": "SQL",
        "description": "warehouse inventory management system",
        "large_table": "stock_movements",
        "large_table_rows": "18 million",
        "large_table_filter_col": "warehouse_id",
        "large_table_filter_type": "INT NOT NULL",
        "join_table": "movement_items",
        "join_table_rows": "60 million",
        "join_fk_col": "movement_id",
        "join_fk_type": "INT NOT NULL",
        "ts_table": "audit_logs",
        "ts_table_rows": "25 million",
        "ts_col": "logged_at",
        "ts_col_type": "TIMESTAMP NOT NULL",
        "composite_table": "items",
        "composite_table_rows": "3 million",
        "composite_col1": "category_id",
        "composite_col2": "location_id",
        "composite_col1_type": "INT NOT NULL",
        "composite_col2_type": "INT NOT NULL",
        "small_table": "warehouse_zones",
        "small_table_rows": "16",
        "small_table_desc": "warehouse zone reference (16 rows)",
        "small_filter_col": "zone_code",
        "summary_table": "quarterly_stock_summary",
        "summary_table_rows": "40",
        "summary_table_desc": "quarterly stock level aggregates (40 rows)",
        "summary_col": "quarter_start",
        "schema_change": "stock_movements table had warehouse_id added to support multi-warehouse operations; the new FK column has no index",
        "product_name": "StockMaster",
    },
    {
        "name": "billing",
        "language": "SQL",
        "description": "subscription billing platform",
        "large_table": "invoices",
        "large_table_rows": "9 million",
        "large_table_filter_col": "account_id",
        "large_table_filter_type": "INT NOT NULL",
        "join_table": "invoice_line_items",
        "join_table_rows": "35 million",
        "join_fk_col": "invoice_id",
        "join_fk_type": "INT NOT NULL",
        "ts_table": "payment_attempts",
        "ts_table_rows": "6 million",
        "ts_col": "attempted_at",
        "ts_col_type": "TIMESTAMP NOT NULL",
        "composite_table": "subscriptions",
        "composite_table_rows": "4 million",
        "composite_col1": "plan_id",
        "composite_col2": "status",
        "composite_col1_type": "INT NOT NULL",
        "composite_col2_type": "VARCHAR(20) NOT NULL",
        "small_table": "billing_cycles",
        "small_table_rows": "6",
        "small_table_desc": "billing cycle reference (6 rows — monthly, quarterly, annual, etc.)",
        "small_filter_col": "cycle_code",
        "summary_table": "annual_revenue_summary",
        "summary_table_rows": "10",
        "summary_table_desc": "annual revenue aggregates (10 rows)",
        "summary_col": "fiscal_year",
        "schema_change": "invoices table had account_id column added during account hierarchy migration; the new FK column has no index",
        "product_name": "BillingEngine",
    },
]

# Bug sets: indexes_needed controls which of Q1-Q4 need indexes
# Q1=large_table_filter, Q2=join_fk, Q3=ts_range, Q4=composite (optional)
INDEX_SETS = [
    {"needs_q4": True,  "label": "4-index"},   # seed 0: all 4
    {"needs_q4": False, "label": "3-index"},   # seed 1: Q1-Q3 only
    {"needs_q4": True,  "label": "4-index"},   # seed 2: all 4
    {"needs_q4": False, "label": "3-index"},   # seed 3: Q1-Q3 only
    {"needs_q4": True,  "label": "4-index"},   # seed 4: all 4
]


class Generator(TaskGenerator):
    task_id = "DB2_query_regression"
    domain = "Database"
    difficulty = "hard"
    languages = ["sql", "python"]

    @staticmethod
    def _clean(s: str) -> str:
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        idx_set = INDEX_SETS[seed % len(INDEX_SETS)]
        cfg = DOMAINS[domain_idx]
        needs_q4 = idx_set["needs_q4"]

        workspace_files = self._make_workspace(cfg, needs_q4)
        spec_md = self._clean(self._make_spec(cfg, needs_q4))
        brief_md = self._clean(self._make_brief(cfg))

        # Index names the grader checks for
        idx_q1 = f"idx_{cfg['large_table']}_{cfg['large_table_filter_col']}"
        idx_q2 = f"idx_{cfg['join_table']}_{cfg['join_fk_col']}"
        idx_q3 = f"idx_{cfg['ts_table']}_{cfg['ts_col']}"
        idx_q4 = f"idx_{cfg['composite_table']}_{cfg['composite_col1']}_{cfg['composite_col2']}"

        required_indexes = [idx_q1, idx_q2, idx_q3]
        if needs_q4:
            required_indexes.append(idx_q4)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "needs_q4": needs_q4,
                "required_indexes": required_indexes,
                "forbidden_index_tables": [cfg["small_table"], cfg["summary_table"]],
                "small_table": cfg["small_table"],
                "summary_table": cfg["summary_table"],
                "large_table": cfg["large_table"],
                "join_table": cfg["join_table"],
                "ts_table": cfg["ts_table"],
                "composite_table": cfg["composite_table"],
                "idx_q1": idx_q1,
                "idx_q2": idx_q2,
                "idx_q3": idx_q3,
                "idx_q4": idx_q4 if needs_q4 else None,
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "Database"},
        )

    # ── Workspace files ────────────────────────────────────────────────────────

    def _make_workspace(self, cfg: dict, needs_q4: bool) -> dict:
        files = {}
        files["schema.sql"] = self._clean(self._make_schema(cfg))
        files["queries.sql"] = self._clean(self._make_queries(cfg, needs_q4))
        files["dba_analysis.md"] = self._clean(self._make_dba_analysis(cfg, needs_q4))
        files["README.md"] = self._clean(self._make_readme(cfg))
        return files

    def _make_schema(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            -- Schema for {c['description']}
            -- Generated for DB2_query_regression task
            -- Note: This schema reflects the state AFTER the recent schema change.
            -- The schema change introduced new columns without corresponding indexes.

            -- ── Large table (primary query target) ─────────────────────────────
            CREATE TABLE IF NOT EXISTS {c['large_table']} (
                id BIGINT PRIMARY KEY,
                {c['large_table_filter_col']} {c['large_table_filter_type']},
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                amount NUMERIC(12,2),
                notes TEXT
            );
            -- Approximate row count: {c['large_table_rows']}
            -- Schema change: {c['schema_change']}

            -- ── Join table (high-volume join target) ────────────────────────────
            CREATE TABLE IF NOT EXISTS {c['join_table']} (
                id BIGINT PRIMARY KEY,
                {c['join_fk_col']} {c['join_fk_type']},
                quantity INT NOT NULL DEFAULT 1,
                unit_price NUMERIC(10,2),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            -- Approximate row count: {c['join_table_rows']}

            -- ── Timestamp-range table ────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS {c['ts_table']} (
                id BIGINT PRIMARY KEY,
                {c['ts_col']} {c['ts_col_type']},
                event_type VARCHAR(50),
                actor_id BIGINT,
                payload JSONB
            );
            -- Approximate row count: {c['ts_table_rows']}

            -- ── Composite-filter table ────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS {c['composite_table']} (
                id BIGINT PRIMARY KEY,
                {c['composite_col1']} {c['composite_col1_type']},
                {c['composite_col2']} {c['composite_col2_type']},
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            -- Approximate row count: {c['composite_table_rows']}

            -- ── Small reference table (seq scan intentional) ─────────────────────
            CREATE TABLE IF NOT EXISTS {c['small_table']} (
                id INT PRIMARY KEY,
                {c['small_filter_col']} VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE
            );
            -- Approximate row count: {c['small_table_rows']} rows
            -- DBA note: Sequential scan is optimal for this table size.
            -- Adding an index would add write overhead with no read benefit.

            -- ── Summary/aggregation table (seq scan intentional) ─────────────────
            CREATE TABLE IF NOT EXISTS {c['summary_table']} (
                id SERIAL PRIMARY KEY,
                {c['summary_col']} DATE NOT NULL UNIQUE,
                total_count BIGINT NOT NULL DEFAULT 0,
                total_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
                avg_amount NUMERIC(10,2),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            -- Approximate row count: {c['summary_table_rows']} rows
            -- DBA note: This table is always fully scanned for aggregation queries.
            -- An index on {c['summary_col']} would not help because queries read all rows.
            """)

    def _make_queries(self, cfg: dict, needs_q4: bool) -> str:
        c = cfg
        q4_block = ""
        if needs_q4:
            q4_block = textwrap.dedent(f"""\

                -- Q4: Composite filter on {c['composite_table']}
                -- Status: REGRESSION — sequential scan on {c['composite_table_rows']} rows
                -- Expected: index scan on ({c['composite_col1']}, {c['composite_col2']})
                -- EXPLAIN shows: Seq Scan on {c['composite_table']} (cost=0.00..89432.00 rows=3217841)
                SELECT id, name, {c['composite_col1']}, {c['composite_col2']}
                FROM {c['composite_table']}
                WHERE {c['composite_col1']} = $1
                  AND {c['composite_col2']} = $2
                ORDER BY name;
                """)

        return textwrap.dedent(f"""\
            -- Queries exhibiting performance regressions after schema change
            -- See dba_analysis.md for EXPLAIN output and recommendations

            -- Q1: Filter on {c['large_table']} by {c['large_table_filter_col']}
            -- Status: REGRESSION — sequential scan on {c['large_table_rows']} rows
            -- Expected: index scan on {c['large_table_filter_col']}
            -- EXPLAIN shows: Seq Scan on {c['large_table']} (cost=0.00..342891.00 rows=12000000)
            SELECT id, {c['large_table_filter_col']}, status, amount
            FROM {c['large_table']}
            WHERE {c['large_table_filter_col']} = $1
            ORDER BY created_at DESC
            LIMIT 50;

            -- Q2: Join {c['large_table']} → {c['join_table']} via {c['join_fk_col']}
            -- Status: REGRESSION — no index on FK column after schema change
            -- Expected: index scan on {c['join_table']}.{c['join_fk_col']}
            -- EXPLAIN shows: Hash Join → Seq Scan on {c['join_table']} (cost=0.00..1289432.00 rows=45000000)
            SELECT o.id, o.status, li.quantity, li.unit_price
            FROM {c['large_table']} o
            JOIN {c['join_table']} li ON li.{c['join_fk_col']} = o.id
            WHERE o.{c['large_table_filter_col']} = $1
              AND o.status = 'active';

            -- Q3: Time-range query on {c['ts_table']}
            -- Status: REGRESSION — sequential scan on {c['ts_table_rows']} rows for range filter
            -- Expected: index scan on {c['ts_col']}
            -- EXPLAIN shows: Seq Scan on {c['ts_table']} (cost=0.00..213891.00 rows=8000000)
            SELECT id, {c['ts_col']}, event_type, actor_id
            FROM {c['ts_table']}
            WHERE {c['ts_col']} >= $1
              AND {c['ts_col']} < $2
            ORDER BY {c['ts_col']} DESC
            LIMIT 100;
            {q4_block}
            -- S1: Lookup on {c['small_table']}
            -- Status: ACCEPTABLE — sequential scan on {c['small_table_rows']} rows
            -- DBA decision: table is tiny; seq scan has lower overhead than index lookup
            -- Do NOT add index to this table
            SELECT id, {c['small_filter_col']}, description
            FROM {c['small_table']}
            WHERE {c['small_filter_col']} = $1
              AND active = TRUE;

            -- S2: Aggregation over {c['summary_table']}
            -- Status: ACCEPTABLE — full table scan intentional for aggregation
            -- DBA decision: all rows are read; index would add write overhead with no benefit
            -- Do NOT add index to this table
            SELECT
                DATE_TRUNC('month', {c['summary_col']}) AS month,
                SUM(total_count) AS month_count,
                SUM(total_amount) AS month_amount
            FROM {c['summary_table']}
            GROUP BY DATE_TRUNC('month', {c['summary_col']})
            ORDER BY month DESC;
            """)

    def _make_dba_analysis(self, cfg: dict, needs_q4: bool) -> str:
        c = cfg
        q4_section = ""
        if needs_q4:
            q4_section = textwrap.dedent(f"""\

                ### Q4 — Composite Filter on `{c['composite_table']}`

                **Query:** Filter by `({c['composite_col1']}, {c['composite_col2']})` on `{c['composite_table']}`
                **Table size:** ~{c['composite_table_rows']} rows
                **Current plan:** `Seq Scan on {c['composite_table']}  (cost=0.00..89432.00 rows=3217841 width=48)`
                **Root cause:** No composite index on `({c['composite_col1']}, {c['composite_col2']})`.
                **Recommendation:** Create index:
                ```sql
                CREATE INDEX idx_{c['composite_table']}_{c['composite_col1']}_{c['composite_col2']}
                    ON {c['composite_table']} ({c['composite_col1']}, {c['composite_col2']});
                ```
                **Expected plan after fix:** `Index Scan using idx_{c['composite_table']}_{c['composite_col1']}_{c['composite_col2']}` (cost~5–20)
                """)

        return textwrap.dedent(f"""\
            # DBA Performance Analysis — {c['product_name']}

            ## Background

            A recent schema change was deployed: {c['schema_change']}.
            After the deployment, several queries regressed from fast index scans to
            slow sequential scans. This document identifies which regressions require
            index creation and which are acceptable sequential scans that should NOT
            be indexed.

            ## Genuine Regressions (Indexes Required)

            ### Q1 — Filter on `{c['large_table']}.{c['large_table_filter_col']}`

            **Query:** SELECT from `{c['large_table']}` filtered by `{c['large_table_filter_col']}`
            **Table size:** ~{c['large_table_rows']} rows
            **Current plan:** `Seq Scan on {c['large_table']}  (cost=0.00..342891.00 rows=12000000 width=72)`
            **Root cause:** The schema change added `{c['large_table_filter_col']}` as a new column
            but no index was created. Queries filtering by this column now scan the entire table.
            **Recommendation:** Create index:
            ```sql
            CREATE INDEX idx_{c['large_table']}_{c['large_table_filter_col']}
                ON {c['large_table']} ({c['large_table_filter_col']});
            ```
            **Expected plan after fix:** `Index Scan using idx_{c['large_table']}_{c['large_table_filter_col']}` (cost~0.56–8.58)

            ### Q2 — Join `{c['large_table']}` → `{c['join_table']}` via `{c['join_fk_col']}`

            **Query:** JOIN from `{c['join_table']}` on `{c['join_fk_col']}`
            **Table size:** ~{c['join_table_rows']} rows
            **Current plan:** `Hash Join  (cost=0.00..1289432.00 rows=45000000 width=28)`
            **Root cause:** FK column `{c['join_table']}.{c['join_fk_col']}` has no index.
            Every join requires a full scan of `{c['join_table']}`.
            **Recommendation:** Create index:
            ```sql
            CREATE INDEX idx_{c['join_table']}_{c['join_fk_col']}
                ON {c['join_table']} ({c['join_fk_col']});
            ```
            **Expected plan after fix:** `Index Scan using idx_{c['join_table']}_{c['join_fk_col']}` (cost~0.56–12.21)

            ### Q3 — Time-Range Query on `{c['ts_table']}.{c['ts_col']}`

            **Query:** SELECT from `{c['ts_table']}` with timestamp range filter
            **Table size:** ~{c['ts_table_rows']} rows
            **Current plan:** `Seq Scan on {c['ts_table']}  (cost=0.00..213891.00 rows=8000000 width=64)`
            **Root cause:** No index on `{c['ts_col']}`. Range queries (`BETWEEN`, `>=`, `<`)
            cannot use the primary key and scan the entire table.
            **Recommendation:** Create index:
            ```sql
            CREATE INDEX idx_{c['ts_table']}_{c['ts_col']}
                ON {c['ts_table']} ({c['ts_col']});
            ```
            **Expected plan after fix:** `Index Scan using idx_{c['ts_table']}_{c['ts_col']}` (cost~0.56–15.33)
            {q4_section}
            ## Acceptable Sequential Scans (Do NOT Add Indexes)

            ### S1 — Lookup on `{c['small_table']}`

            **Query:** SELECT from `{c['small_table']}` by `{c['small_filter_col']}`
            **Table size:** {c['small_table_rows']} rows — {c['small_table_desc']}
            **Current plan:** `Seq Scan on {c['small_table']}  (cost=0.00..1.12 rows=1 width=48)`
            **Decision:** ACCEPTABLE — no action required.
            **Rationale:** At {c['small_table_rows']} rows, the table fits in a single memory page.
            PostgreSQL's planner correctly chooses a sequential scan because the index
            lookup overhead (buffer pin, index page read, heap fetch) exceeds the cost of
            simply reading all {c['small_table_rows']} rows. Adding an index would increase write
            latency on every INSERT/UPDATE with zero read benefit.

            ### S2 — Aggregation over `{c['summary_table']}`

            **Query:** GROUP BY aggregation over `{c['summary_table']}`
            **Table size:** {c['summary_table_rows']} rows — {c['summary_table_desc']}
            **Current plan:** `Seq Scan on {c['summary_table']}  (cost=0.00..1.{len(c['summary_table_rows'])*2} rows={c['summary_table_rows']} width=40)`
            **Decision:** ACCEPTABLE — no action required.
            **Rationale:** The aggregation query reads every row in the table to compute
            monthly/quarterly totals. An index on `{c['summary_col']}` cannot help a
            full-table aggregation — the planner will ignore it and still scan all rows.
            Adding the index would only add unnecessary overhead on writes.

            ## Summary

            | Query | Table | Size | Action |
            |-------|-------|------|--------|
            | Q1 | `{c['large_table']}` | {c['large_table_rows']} | **CREATE INDEX** (regression) |
            | Q2 | `{c['join_table']}` | {c['join_table_rows']} | **CREATE INDEX** (regression) |
            | Q3 | `{c['ts_table']}` | {c['ts_table_rows']} | **CREATE INDEX** (regression) |
            {"| Q4 | `" + c['composite_table'] + "` | " + c['composite_table_rows'] + " | **CREATE INDEX** (regression) |" if needs_q4 else ""}
            | S1 | `{c['small_table']}` | {c['small_table_rows']} rows | **DO NOT INDEX** (acceptable) |
            | S2 | `{c['summary_table']}` | {c['summary_table_rows']} rows | **DO NOT INDEX** (acceptable) |

            ## Deliverables

            Create a file `indexes.sql` containing only the `CREATE INDEX` statements
            for the genuine regressions (Q1, Q2, Q3{"" if not needs_q4 else ", Q4"}).
            Do NOT include indexes for `{c['small_table']}` or `{c['summary_table']}`.
            """)

    def _make_readme(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # {cfg['product_name']} — DB Performance Task

            This workspace contains the schema and queries for a {cfg['description']}.

            ## Files

            - `schema.sql` — database schema (read-only; do not modify)
            - `queries.sql` — queries experiencing performance issues (read-only)
            - `dba_analysis.md` — DBA EXPLAIN analysis and recommendations
            - `indexes.sql` — **create this file** with your `CREATE INDEX` statements

            ## Task

            Several queries are experiencing performance regressions after a recent
            schema change. Analyze `dba_analysis.md` to determine which queries need
            indexes and which are acceptable sequential scans.

            ## Deliverable

            Create `indexes.sql` with the appropriate `CREATE INDEX` statements.
            Do NOT create indexes on small reference tables where a sequential scan
            is more efficient — see `dba_analysis.md` for the full analysis.
            """)

    # ── Spec / Brief ──────────────────────────────────────────────────────────

    def _make_spec(self, cfg: dict, needs_q4: bool) -> str:
        c = cfg
        idx_q1 = f"idx_{c['large_table']}_{c['large_table_filter_col']}"
        idx_q2 = f"idx_{c['join_table']}_{c['join_fk_col']}"
        idx_q3 = f"idx_{c['ts_table']}_{c['ts_col']}"
        idx_q4 = f"idx_{c['composite_table']}_{c['composite_col1']}_{c['composite_col2']}"

        q4_row = ""
        q4_detail = ""
        if needs_q4:
            q4_row = f"| Q4 | {c['composite_table']} | `({c['composite_col1']}, {c['composite_col2']})` | `{idx_q4}` |"
            q4_detail = textwrap.dedent(f"""\

                #### Q4 — `{c['composite_table']}` composite index

                Add `CREATE INDEX {idx_q4} ON {c['composite_table']} ({c['composite_col1']}, {c['composite_col2']});`
                """)

        return textwrap.dedent(f"""\
            # DB2_query_regression: Query Performance Regression Fix — Full Specification (Planner Only)

            ## Overview

            A schema change to the {c['description']} introduced new columns without
            corresponding indexes. This caused {3 if not needs_q4 else 4} query regressions.
            Two other queries have acceptable sequential scans and must NOT be indexed.

            The executor only receives the brief; this spec provides the full analysis.

            ## File Structure

            - `schema.sql` — database schema (read-only)
            - `queries.sql` — slow queries (read-only)
            - `dba_analysis.md` — DBA EXPLAIN analysis (readable by agents)
            - `indexes.sql` — **agent must create this file**

            ## Schema Change Context

            {c['schema_change']}

            ## Genuine Regressions (Indexes Required)

            | Query | Table | Index Column(s) | Index Name |
            |-------|-------|-----------------|------------|
            | Q1 | {c['large_table']} | `{c['large_table_filter_col']}` | `{idx_q1}` |
            | Q2 | {c['join_table']} | `{c['join_fk_col']}` | `{idx_q2}` |
            | Q3 | {c['ts_table']} | `{c['ts_col']}` | `{idx_q3}` |
            {q4_row}

            ### Index Details

            #### Q1 — `{c['large_table']}.{c['large_table_filter_col']}`

            Add `CREATE INDEX {idx_q1} ON {c['large_table']} ({c['large_table_filter_col']});`

            #### Q2 — `{c['join_table']}.{c['join_fk_col']}`

            Add `CREATE INDEX {idx_q2} ON {c['join_table']} ({c['join_fk_col']});`

            #### Q3 — `{c['ts_table']}.{c['ts_col']}`

            Add `CREATE INDEX {idx_q3} ON {c['ts_table']} ({c['ts_col']});`
            {q4_detail}
            ## Acceptable Sequential Scans (DO NOT INDEX)

            | Query | Table | Reason |
            |-------|-------|--------|
            | S1 | `{c['small_table']}` | Only {c['small_table_rows']} rows — seq scan is optimal |
            | S2 | `{c['summary_table']}` | Full aggregation scan — index unused by planner |

            **Critical:** Adding indexes to `{c['small_table']}` or `{c['summary_table']}` is
            **incorrect** and will fail grading. The DBA analysis explicitly documents why
            these tables should not be indexed.

            ## Acceptance Criteria

            1. `indexes.sql` exists in the workspace root
            2. `indexes.sql` contains CREATE INDEX for Q1, Q2, Q3{"" if not needs_q4 else ", Q4"}
            3. `indexes.sql` does NOT contain CREATE INDEX on `{c['small_table']}`
            4. `indexes.sql` does NOT contain CREATE INDEX on `{c['summary_table']}`
            5. All index names match the expected format `idx_<table>_<column(s)>`
            6. `schema.sql` and `queries.sql` are NOT modified

            ## Authoritative Sources

            - This spec is the authoritative analysis of which queries need indexes
            - `dba_analysis.md` provides the same analysis (readable by agents)
            - The DBA decision on small tables is final — do not second-guess it
            """)

    def _make_brief(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # DB2_query_regression (Brief)

            Several queries in the {cfg['description']} are running slowly after a
            recent schema change. Optimize the slow queries.

            **Reference:** `dba_analysis.md` contains EXPLAIN output and recommendations.

            **Deliverable:** Create `indexes.sql` with the appropriate `CREATE INDEX`
            statements. Do NOT modify `schema.sql` or `queries.sql`.

            Follow the Planner's guidance precisely.
            """)
