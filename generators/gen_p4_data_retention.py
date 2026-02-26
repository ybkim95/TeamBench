"""
Parameterized generator for P4: Data Retention Policy Implementation.

Each seed produces:
  - Different data types with distinct retention periods
  - Different deletion ORDER requirements (anonymize-before-delete,
    cascade-dependents-first, audit-log-before-deletion)
  - Different exemption types (legal hold overrides deletion)
  - A SQLite-backed Python app with no retention logic
  - expected.json with ground-truth for grading

TNI Pattern E,F:
  - Spec has per-data-type retention periods (user PII: 30 days after deletion
    request, logs: 90 days, analytics: 1 year, financial: 7 years)
  - Deletion ORDER (must anonymize before delete, must cascade to dependent
    records first, must create audit log entries before deletion)
  - Exemptions (legal hold overrides deletion)
  - Brief says only "Implement the data retention policy for the application."
"""
from __future__ import annotations

import json
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Data-type pool ─────────────────────────────────────────────────────────────

DATA_TYPE_POOL = [
    # (type_id, label, base_retention_days, unit_label, description, table_name, has_pii)
    ("user_pii",     "User PII",            30,    "days after deletion request",
     "Personally identifiable user profile data (name, email, address)",
     "user_profiles", True),
    ("access_logs",  "Access Logs",         90,    "days",
     "HTTP access and authentication event logs",
     "access_logs", False),
    ("error_logs",   "Error Logs",          60,    "days",
     "Application error and exception logs",
     "error_logs", False),
    ("audit_logs",   "Audit Logs",          365,   "days",
     "Compliance audit trail entries — must never be modified, only appended",
     "audit_trail", False),
    ("analytics",    "Analytics Data",      365,   "days",
     "Aggregated usage and behavioural analytics events",
     "analytics_events", False),
    ("financial",    "Financial Records",   2555,  "days",
     "Payment transactions, invoices, billing records (7 years statutory)",
     "financial_records", True),
    ("session_data", "Session Data",        7,     "days",
     "Temporary user session tokens and state",
     "user_sessions", False),
    ("backups",      "Backup Snapshots",    180,   "days",
     "Database backup and snapshot archives",
     "backup_snapshots", False),
    ("user_content", "User-Generated Content", 90, "days after account deletion",
     "Files, posts, and documents created by users",
     "user_content", True),
    ("telemetry",    "Telemetry Data",      30,    "days",
     "Device and feature usage telemetry",
     "telemetry_events", False),
    ("support_tickets", "Support Tickets",  730,   "days",
     "Customer support interactions and attachments",
     "support_tickets", False),
    ("marketing",    "Marketing Data",      180,   "days",
     "Email campaign records and opt-in preferences",
     "marketing_records", True),
]

# ── Exemption type pool ────────────────────────────────────────────────────────

EXEMPTION_POOL = [
    # (exemption_type, label, description)
    ("legal_hold",       "Legal Hold",
     "Records under active litigation hold must not be deleted regardless of retention age."),
    ("regulatory_audit", "Regulatory Audit Lock",
     "Records flagged for a pending regulatory audit are exempt until the audit closes."),
    ("active_dispute",   "Active Dispute Flag",
     "Records tied to an unresolved billing or service dispute are exempt from deletion."),
    ("consent_pending",  "Consent Review Pending",
     "Records awaiting re-consent confirmation must be retained until consent is resolved."),
    ("tax_investigation","Tax Investigation Hold",
     "Financial records under active tax investigation are exempt from scheduled deletion."),
]

# ── Deletion order rules (always all three; wording varies slightly per seed) ──

ORDER_VARIANTS = [
    # (anonymize_phrase, cascade_phrase, audit_phrase)
    (
        "All PII fields must be anonymized (replaced with placeholder tokens) BEFORE "
        "the record row is hard-deleted from the database.",
        "Dependent child records (records referencing the parent via foreign key) must be "
        "deleted BEFORE the parent record is removed.",
        "An audit log entry recording the deletion event (record_type, record_id, "
        "deletion_timestamp, triggered_by) must be written BEFORE the delete is committed.",
    ),
    (
        "PII fields (name, email, phone, address) must be overwritten with anonymization "
        "tokens prior to physical row deletion. Anonymization must precede deletion.",
        "Child records that reference a parent must be purged first; the parent row may "
        "only be removed after all referencing children are gone.",
        "A retention audit entry must be persisted to the audit trail before any deletion "
        "is executed. The audit entry must include: data_type, record_id, reason, timestamp.",
    ),
    (
        "Before hard-deleting any record, replace all personal data fields with the "
        "sentinel value '[REDACTED]'. The anonymization step is mandatory and must "
        "complete before the DELETE statement runs.",
        "The cascade order is strict: delete dependent child records first, then delete "
        "the parent. Never delete a parent row while children still reference it.",
        "Each deletion must be preceded by an audit log write. The audit log entry must "
        "be committed before the deletion transaction commits.",
    ),
]


class Generator(TaskGenerator):
    task_id = "P4_data_retention"
    domain = "policy"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # ── Pick data types for this seed (5-7 types) ──────────────────────────
        num_types = rng.randint(5, 7)
        selected_types = rng.sample(DATA_TYPE_POOL, num_types)
        # Always include financial (for 7-year rule) and one PII type
        has_financial = any(dt[0] == "financial" for dt in selected_types)
        has_pii = any(dt[6] for dt in selected_types)
        if not has_financial:
            financial = next(dt for dt in DATA_TYPE_POOL if dt[0] == "financial")
            selected_types[-1] = financial
        if not has_pii:
            pii_opts = [dt for dt in DATA_TYPE_POOL if dt[6] and dt[0] != "financial"]
            selected_types[-2] = rng.choice(pii_opts)
        # Deduplicate after forced insertions
        seen_ids: set[str] = set()
        deduped = []
        for dt in selected_types:
            if dt[0] not in seen_ids:
                seen_ids.add(dt[0])
                deduped.append(dt)
        selected_types = deduped

        # ── Apply per-seed retention period jitter (±10-20%) ──────────────────
        # For most types; financial stays at exactly 2555 (7 years statutory)
        retention_config: dict[str, dict] = {}
        for dt in selected_types:
            type_id, label, base_days, unit, desc, table, has_pii_flag = dt
            if type_id == "financial":
                days = 2555  # immutable statutory
            else:
                jitter = rng.randint(-int(base_days * 0.1), int(base_days * 0.2))
                days = max(7, base_days + jitter)
            retention_config[type_id] = {
                "label": label,
                "retention_days": days,
                "unit_label": unit,
                "description": desc,
                "table_name": table,
                "has_pii": has_pii_flag,
            }

        # ── Pick exemption types (2-3) ─────────────────────────────────────────
        num_exemptions = rng.randint(2, 3)
        selected_exemptions = rng.sample(EXEMPTION_POOL, num_exemptions)
        # Always include legal_hold
        has_legal = any(e[0] == "legal_hold" for e in selected_exemptions)
        if not has_legal:
            legal = next(e for e in EXEMPTION_POOL if e[0] == "legal_hold")
            selected_exemptions[-1] = legal

        exemptions = [
            {"type": e[0], "label": e[1], "description": e[2]}
            for e in selected_exemptions
        ]

        # ── Pick deletion order variant ────────────────────────────────────────
        order_idx = seed % len(ORDER_VARIANTS)
        order_variant = ORDER_VARIANTS[order_idx]
        anonymize_rule, cascade_rule, audit_rule = order_variant

        # ── Determine which types need anonymization before deletion ──────────
        pii_types = [tid for tid, cfg in retention_config.items() if cfg["has_pii"]]

        # ── Build expected values ──────────────────────────────────────────────
        expected = {
            "retention_config": retention_config,
            "exemptions": exemptions,
            "pii_types": pii_types,
            "deletion_order": {
                "step1": "write_audit_log",
                "step2": "delete_dependents",
                "step3": "anonymize_pii",
                "step4": "delete_record",
            },
            "legal_hold_exempt": True,
            "checks": {
                "retention_periods_correct": True,
                "audit_log_before_deletion": True,
                "cascade_dependents_first": True,
                "anonymize_before_delete": True,
                "legal_hold_prevents_deletion": True,
                "exempt_records_untouched": True,
            },
        }

        # ── Generate corpus/retention_policy.txt ──────────────────────────────
        policy_txt = self._generate_policy(
            retention_config=retention_config,
            exemptions=exemptions,
            anonymize_rule=anonymize_rule,
            cascade_rule=cascade_rule,
            audit_rule=audit_rule,
            seed=seed,
        )

        # ── Generate workspace files ───────────────────────────────────────────
        app_py = self._generate_app(retention_config, exemptions)
        seed_sql = self._generate_seed_sql(retention_config, seed)

        spec_md = self._generate_spec(
            retention_config=retention_config,
            exemptions=exemptions,
            anonymize_rule=anonymize_rule,
            cascade_rule=cascade_rule,
            audit_rule=audit_rule,
        )
        brief_md = self._generate_brief()

        corpus_files = {
            "retention_policy.txt": policy_txt,
        }

        workspace_files = {
            "retention.py": app_py,
            "seed_data.sql": seed_sql,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
            corpus_files=corpus_files,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _generate_policy(
        self,
        retention_config: dict,
        exemptions: list,
        anonymize_rule: str,
        cascade_rule: str,
        audit_rule: str,
        seed: int,
    ) -> str:
        ver = f"{1 + seed % 4}.{seed % 9}"
        year = 2025 + (seed % 3)

        lines = [
            "DATA RETENTION POLICY",
            f"Version: {ver}",
            f"Effective Date: {year}-01-01",
            "Classification: INTERNAL — COMPLIANCE SENSITIVE",
            "",
            "=== PURPOSE ===",
            "",
            "This policy defines mandatory retention periods for each category of data",
            "stored by the application, the required deletion procedure, and exemptions",
            "that override scheduled deletion.",
            "",
            "=== SECTION 1: RETENTION PERIODS ===",
            "",
            "Each data type has a mandatory minimum retention period. Data MUST NOT be",
            "deleted before its retention period expires. Data SHOULD be deleted within",
            "30 days after the retention period expires (unless exempt).",
            "",
        ]

        for type_id, cfg in retention_config.items():
            lines.append(f"Data Type: {cfg['label']} (table: {cfg['table_name']})")
            lines.append(f"  Retention Period: {cfg['retention_days']} {cfg['unit_label']}")
            lines.append(f"  Description: {cfg['description']}")
            if cfg["has_pii"]:
                lines.append("  PII Flag: YES — this data type contains personally identifiable information.")
            else:
                lines.append("  PII Flag: NO")
            lines.append("")

        lines += [
            "=== SECTION 2: DELETION PROCEDURE (MANDATORY ORDER) ===",
            "",
            "The deletion procedure MUST follow these steps in STRICT ORDER.",
            "Skipping or reordering steps constitutes a compliance violation.",
            "",
            "Step 1 — Write Audit Log Entry:",
            f"  {audit_rule}",
            "",
            "Step 2 — Delete Dependent Records (Cascade):",
            f"  {cascade_rule}",
            "",
            "Step 3 — Anonymize PII Fields (applies to PII data types only):",
            f"  {anonymize_rule}",
            "",
            "Step 4 — Hard Delete the Record:",
            "  Only after steps 1-3 are complete may the record be physically removed",
            "  from the primary table.",
            "",
            "=== SECTION 3: EXEMPTIONS ===",
            "",
            "The following exemptions override scheduled deletion. An exempt record",
            "MUST NOT be deleted regardless of how far past its retention period it is.",
            "",
        ]

        for i, ex in enumerate(exemptions, 1):
            lines.append(f"Exemption {i}: {ex['label']}")
            lines.append(f"  Type ID: {ex['type']}")
            lines.append(f"  Rule: {ex['description']}")
            lines.append("")

        lines += [
            "=== SECTION 4: IMPLEMENTATION REQUIREMENTS ===",
            "",
            "1. The function `run_retention()` in retention.py must identify all records",
            "   past their retention period and process each one through the 4-step",
            "   deletion procedure above.",
            "2. Before deleting any record, check all exemption flags on that record.",
            "   If any exemption is active, SKIP the record entirely.",
            "3. PII anonymization applies only to data types with PII Flag: YES.",
            "   For non-PII data types, skip step 3 and proceed directly to step 4.",
            "4. The audit log table (retention_audit) must be written to before the",
            "   deletion transaction commits. Required fields:",
            "     - data_type (string): the DATA_TYPE value from the record",
            "     - record_id (integer): the id of the deleted record",
            "     - action (string): one of 'anonymized', 'deleted', 'skipped_exempt'",
            "     - reason (string): human-readable reason for the action",
            "     - processed_at (ISO-8601 datetime string)",
            "5. The function must return a summary dict with keys:",
            "     - deleted: count of records hard-deleted",
            "     - anonymized: count of records anonymized (PII types)",
            "     - skipped_exempt: count of records skipped due to exemption",
            "     - audit_entries_written: count of audit log entries created",
            "",
            "=== END OF POLICY ===",
        ]

        return "\n".join(lines) + "\n"

    def _generate_app(self, retention_config: dict, exemptions: list) -> str:
        """Generate retention.py workspace stub — no retention logic implemented."""

        type_ids = list(retention_config.keys())
        type_ids_repr = ", ".join(f'"{t}"' for t in type_ids)

        exemption_types = [e["type"] for e in exemptions]
        exemption_repr = ", ".join(f'"{e}"' for e in exemption_types)

        retention_map_lines = []
        for type_id, cfg in retention_config.items():
            retention_map_lines.append(
                f'    "{type_id}": {cfg["retention_days"]},  # {cfg["label"]}'
            )
        retention_map_str = "\n".join(retention_map_lines)

        pii_types = [tid for tid, cfg in retention_config.items() if cfg["has_pii"]]
        pii_repr = ", ".join(f'"{t}"' for t in pii_types)

        table_map_lines = []
        for type_id, cfg in retention_config.items():
            table_map_lines.append(
                f'    "{type_id}": "{cfg["table_name"]}",  # {cfg["label"]}'
            )
        table_map_str = "\n".join(table_map_lines)

        return f'''"""
Data Retention Policy Implementation

This module manages data lifecycle according to the retention policy defined in
corpus/retention_policy.txt.

Your task: implement the `run_retention(db_path)` function so it:
1. Identifies all records past their retention period in each data table.
2. Processes each expired, non-exempt record through the MANDATORY 4-step
   deletion procedure (see corpus/retention_policy.txt Section 2).
3. Skips records that have any active exemption flag set.
4. Returns a summary dict with counts: deleted, anonymized, skipped_exempt,
   audit_entries_written.

The database schema is initialised by seed_data.sql.
Run this module directly to execute retention on the default DB:
  python retention.py [db_path]
"""

import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Policy constants — do NOT change these values; they come from the policy doc.
# ---------------------------------------------------------------------------

# Retention period in days for each data type
RETENTION_DAYS: dict[str, int] = {{
{retention_map_str}
}}

# Data types that contain PII and require anonymization before deletion
PII_TYPES: set[str] = {{{pii_repr}}}

# Table names for each data type
TABLE_NAMES: dict[str, str] = {{
{table_map_str}
}}

# Exemption column names that, when truthy, prevent deletion
EXEMPTION_COLUMNS: list[str] = [{exemption_repr}]


# ---------------------------------------------------------------------------
# Database helpers (do not modify)
# ---------------------------------------------------------------------------

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# TODO: Implement the functions below according to corpus/retention_policy.txt
# ---------------------------------------------------------------------------

def is_exempt(record: sqlite3.Row) -> bool:
    """Return True if the record has any active exemption that prevents deletion."""
    # TODO: check each column in EXEMPTION_COLUMNS; return True if any is truthy
    return False  # placeholder


def write_audit_entry(
    conn: sqlite3.Connection,
    data_type: str,
    record_id: int,
    action: str,
    reason: str,
) -> None:
    """Write a single audit log entry to retention_audit BEFORE deletion."""
    # TODO: INSERT into retention_audit with required fields
    pass  # placeholder


def anonymize_record(
    conn: sqlite3.Connection,
    data_type: str,
    record_id: int,
) -> None:
    """Replace PII fields with [REDACTED] sentinel values."""
    # TODO: UPDATE pii columns to "[REDACTED]" for the given record_id
    pass  # placeholder


def delete_dependents(
    conn: sqlite3.Connection,
    data_type: str,
    record_id: int,
) -> None:
    """Delete child records that reference this record before deleting the parent."""
    # TODO: delete from dependent tables first (see schema for foreign key refs)
    pass  # placeholder


def delete_record(
    conn: sqlite3.Connection,
    data_type: str,
    record_id: int,
) -> None:
    """Hard-delete the record from its primary table."""
    # TODO: DELETE FROM table WHERE id = record_id
    pass  # placeholder


def run_retention(db_path: str) -> dict[str, int]:
    """
    Execute the full data retention run.

    Processes every data type in RETENTION_DAYS, identifies expired records,
    applies the 4-step mandatory deletion procedure, and returns a summary.

    Returns:
        dict with keys: deleted, anonymized, skipped_exempt, audit_entries_written
    """
    # TODO: implement full retention logic
    # The mandatory 4-step order for each eligible record:
    #   1. write_audit_entry(...)      — BEFORE deletion
    #   2. delete_dependents(...)      — cascade children first
    #   3. anonymize_record(...)       — only for PII_TYPES
    #   4. delete_record(...)          — hard delete
    # Skip records where is_exempt(record) is True.
    return {{
        "deleted": 0,
        "anonymized": 0,
        "skipped_exempt": 0,
        "audit_entries_written": 0,
    }}


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "retention.db"
    summary = run_retention(db_path)
    print("Retention run complete:", summary)
'''

    def _generate_seed_sql(self, retention_config: dict, seed: int) -> str:
        """Generate seed_data.sql with schema + deterministic test data."""
        rng = SeededRandom(seed + 1000)  # offset to get independent values

        pii_types = {tid for tid, cfg in retention_config.items() if cfg["has_pii"]}

        lines = [
            "-- Seed data for P4 Data Retention task",
            "-- Run: sqlite3 retention.db < seed_data.sql",
            "",
            "PRAGMA foreign_keys = ON;",
            "",
            "-- ── Audit trail table (written to by retention.py) ──────────────────",
            "CREATE TABLE IF NOT EXISTS retention_audit (",
            "    id            INTEGER PRIMARY KEY AUTOINCREMENT,",
            "    data_type     TEXT    NOT NULL,",
            "    record_id     INTEGER NOT NULL,",
            "    action        TEXT    NOT NULL,  -- 'anonymized', 'deleted', 'skipped_exempt'",
            "    reason        TEXT    NOT NULL,",
            "    processed_at  TEXT    NOT NULL   -- ISO-8601 datetime",
            ");",
            "",
        ]

        # Generate tables for each data type
        parent_tables: list[str] = []
        for type_id, cfg in retention_config.items():
            table = cfg["table_name"]
            is_pii = cfg["has_pii"]
            ret_days = cfg["retention_days"]

            parent_tables.append(table)

            lines.append(f"-- ── {cfg['label']} (retention: {ret_days} days) ──────")
            lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
            lines.append("    id             INTEGER PRIMARY KEY AUTOINCREMENT,")
            if is_pii:
                lines.append("    name           TEXT,")
                lines.append("    email          TEXT,")
                lines.append("    address        TEXT,")
            lines.append("    data_type      TEXT    NOT NULL DEFAULT '" + type_id + "',")
            lines.append("    created_at     TEXT    NOT NULL,  -- ISO-8601")
            lines.append("    expires_at     TEXT    NOT NULL,  -- ISO-8601 (created_at + retention)")
            lines.append("    legal_hold     INTEGER NOT NULL DEFAULT 0,")
            # Add the other exemption columns
            for cfg2 in []:
                pass
            lines.append("    regulatory_audit INTEGER NOT NULL DEFAULT 0,")
            lines.append("    active_dispute   INTEGER NOT NULL DEFAULT 0,")
            lines.append("    consent_pending  INTEGER NOT NULL DEFAULT 0,")
            lines.append("    tax_investigation INTEGER NOT NULL DEFAULT 0")
            lines.append(");")
            lines.append("")

            # Seed rows: mix of expired/fresh, exempt/non-exempt
            rows_expired_not_exempt = rng.randint(3, 6)
            rows_fresh = rng.randint(2, 4)
            rows_exempt = rng.randint(1, 3)

            lines.append(f"-- {cfg['label']} rows: {rows_expired_not_exempt} expired (deletable), "
                         f"{rows_fresh} fresh, {rows_exempt} exempt")

            # Expired, non-exempt rows
            for i in range(rows_expired_not_exempt):
                age_days = ret_days + rng.randint(5, 60)
                created = f"2020-01-{(i % 28) + 1:02d}T00:00:00+00:00"
                expires = f"2020-01-{(i % 28) + 1:02d}T00:00:00+00:00"  # clearly in past
                if is_pii:
                    name_val = f"'User{rng.randint(100,999)}'"
                    email_val = f"'user{rng.randint(100,999)}@example.com'"
                    addr_val = f"'123 Street, City'"
                    lines.append(
                        f"INSERT INTO {table} (name, email, address, created_at, expires_at) VALUES "
                        f"({name_val}, {email_val}, {addr_val}, '{created}', '{expires}');"
                    )
                else:
                    lines.append(
                        f"INSERT INTO {table} (created_at, expires_at) VALUES "
                        f"('{created}', '{expires}');"
                    )

            lines.append("")

            # Fresh rows (not yet expired)
            for i in range(rows_fresh):
                lines.append(
                    f"INSERT INTO {table} (created_at, expires_at) VALUES "
                    f"('2099-01-01T00:00:00+00:00', '2099-12-31T00:00:00+00:00');"
                ) if not is_pii else lines.append(
                    f"INSERT INTO {table} (name, email, address, created_at, expires_at) VALUES "
                    f"('ActiveUser', 'active@example.com', '456 Ave', "
                    f"'2099-01-01T00:00:00+00:00', '2099-12-31T00:00:00+00:00');"
                )

            lines.append("")

            # Exempt rows (legal_hold=1 or other exemption)
            for i in range(rows_exempt):
                # Alternate between legal_hold and regulatory_audit
                if i % 2 == 0:
                    exemption_col = "legal_hold"
                else:
                    exemption_col = "regulatory_audit"
                if is_pii:
                    lines.append(
                        f"INSERT INTO {table} (name, email, address, created_at, expires_at, {exemption_col}) VALUES "
                        f"('HeldUser', 'held@example.com', '789 Blvd', "
                        f"'2020-01-01T00:00:00+00:00', '2020-06-01T00:00:00+00:00', 1);"
                    )
                else:
                    lines.append(
                        f"INSERT INTO {table} (created_at, expires_at, {exemption_col}) VALUES "
                        f"('2020-01-01T00:00:00+00:00', '2020-06-01T00:00:00+00:00', 1);"
                    )

            lines.append("")

        # Child (dependent) table: references first parent table for cascade test
        first_table = next(iter(retention_config.values()))["table_name"]
        lines += [
            "-- ── Dependent child records (used to test cascade deletion) ──────────",
            "CREATE TABLE IF NOT EXISTS record_attachments (",
            "    id         INTEGER PRIMARY KEY AUTOINCREMENT,",
            f"    parent_id  INTEGER NOT NULL REFERENCES {first_table}(id) ON DELETE CASCADE,",
            "    file_name  TEXT    NOT NULL,",
            "    created_at TEXT    NOT NULL",
            ");",
            "",
            f"-- Attach a child row to first few expired parent rows in {first_table}",
            f"INSERT INTO record_attachments (parent_id, file_name, created_at)",
            f"  SELECT id, 'attachment_' || id || '.dat', '2020-01-15T00:00:00+00:00'",
            f"  FROM {first_table} WHERE expires_at < '2025-01-01' LIMIT 2;",
            "",
        ]

        return "\n".join(lines) + "\n"

    def _generate_spec(
        self,
        retention_config: dict,
        exemptions: list,
        anonymize_rule: str,
        cascade_rule: str,
        audit_rule: str,
    ) -> str:
        type_list = "\n".join(
            f"- **{cfg['label']}** (`{tid}`, table `{cfg['table_name']}`): "
            f"{cfg['retention_days']} {cfg['unit_label']}"
            + (" — **contains PII**" if cfg["has_pii"] else "")
            for tid, cfg in retention_config.items()
        )
        exemption_list = "\n".join(
            f"- **{e['label']}** (`{e['type']}`): {e['description']}"
            for e in exemptions
        )

        return f"""# P4: Data Retention Policy Implementation

## Goal
Implement `run_retention(db_path)` in `retention.py` so that it enforces the data
retention policy defined in `corpus/retention_policy.txt` against a SQLite database.

## Data Types and Retention Periods

{type_list}

## Deletion Order (MANDATORY — must be followed exactly)

1. **Write Audit Log Entry** (Step 1, always first):
   {audit_rule}

2. **Delete Dependent Records** (Step 2, cascade before parent):
   {cascade_rule}

3. **Anonymize PII Fields** (Step 3, PII data types only):
   {anonymize_rule}

4. **Hard Delete Record** (Step 4, only after steps 1-3 complete):
   Delete the record from its primary table.

## Exemptions

The following flags prevent deletion entirely. If ANY exemption is active on a
record, skip it and write a `skipped_exempt` audit entry.

{exemption_list}

## Hard Requirements

1. `run_retention(db_path)` must process ALL data types in `RETENTION_DAYS`.
2. Records with `expires_at < NOW()` (UTC) are expired and eligible for deletion.
3. Exempt records (any exemption column is truthy) must NOT be deleted; write a
   `skipped_exempt` audit entry for each skipped record.
4. For each eligible record, execute steps 1 → 2 → 3 → 4 IN ORDER.
5. Anonymization (step 3) applies ONLY to data types in `PII_TYPES`.
6. `record_attachments` (child table) must be deleted BEFORE the parent row.
7. The function must return a dict: `{{deleted, anonymized, skipped_exempt,
   audit_entries_written}}`.
8. Implement `is_exempt()`, `write_audit_entry()`, `anonymize_record()`,
   `delete_dependents()`, and `delete_record()` as called by `run_retention()`.

## Files

- `corpus/retention_policy.txt` — authoritative policy (read this first)
- `retention.py` — implement the stub functions here
- `seed_data.sql` — SQLite schema + test data; run `sqlite3 retention.db < seed_data.sql`

## Deliverables

- `retention.py` with all stub functions implemented.
- Verifier must initialise the DB from `seed_data.sql`, call `run_retention()`,
  and produce `output/attestation.json` with verdict and summary counts.
"""

    def _generate_brief(self) -> str:
        return """# P4: Data Retention (Brief)

Implement the data retention policy for the application.

Read `corpus/retention_policy.txt` for all retention periods, deletion order rules,
and exemptions. Implement `run_retention(db_path)` in `retention.py`.
"""
