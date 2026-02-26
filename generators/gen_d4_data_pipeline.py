"""
Parameterized generator for D4: Data Validation Pipeline.

TNI Pattern A,C (Hidden Constraints + Multi-Criteria):
  - Spec has: complete validation ruleset (field types, ranges, regex patterns,
    cross-field constraints, referential integrity, deduplication with priority rules)
  - Brief says: "The data pipeline is producing invalid records. Fix the validation logic."
  - Without the Planner's complete ruleset the Executor fixes obvious issues
    but misses cross-field constraints and priority-based dedup.

Each seed produces:
  - Different data domain (customer_records, financial_transactions,
    sensor_readings, product_catalog)
  - Different column names / field types matching the domain
  - 8-15 validation rules per domain
  - Specific bug types seeded deterministically:
      missing null check, wrong regex, missing cross-field validation,
      wrong dedup logic, missing type coercion
  - workspace/pipeline.py  — buggy validation pipeline
  - workspace/data/input.csv — input with various quality issues
  - workspace/config/rules.json — partial rules (spec has the full set)
  - reports/expected.json — ground-truth for grading (never seen by agents)
"""
from __future__ import annotations

import csv
import io
import json
import re
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom, NamePool, ValuePool

# ── Domain definitions ────────────────────────────────────────────────────────

DOMAINS = {
    "customer_records": {
        "description": "Customer account records for a B2B SaaS platform",
        "fields": {
            "customer_id":  {"type": "string",  "pattern": r"CUST-\d{6}"},
            "company_name": {"type": "string",  "required": True},
            "email":        {"type": "email",   "required": True},
            "country":      {"type": "enum",    "values": ["US", "CA", "UK", "DE", "FR", "AU", "JP"]},
            "zip_code":     {"type": "string",  "pattern": r"\d{5}(-\d{4})?", "cross_field": "country=US requires 5-digit zip"},
            "account_tier": {"type": "enum",    "values": ["free", "pro", "enterprise"]},
            "monthly_spend":{"type": "float",   "min": 0.0, "max": 100000.0},
            "signup_date":  {"type": "date",    "pattern": r"\d{4}-\d{2}-\d{2}"},
        },
        "cross_field_rules": [
            {
                "rule_id": "zip_country",
                "description": "If country=US then zip_code must match 5-digit pattern",
                "condition": "country == 'US'",
                "target_field": "zip_code",
                "target_pattern": r"^\d{5}(-\d{4})?$",
            },
            {
                "rule_id": "enterprise_spend",
                "description": "enterprise tier requires monthly_spend >= 500",
                "condition": "account_tier == 'enterprise'",
                "target_field": "monthly_spend",
                "target_min": 500.0,
            },
        ],
        "dedup_key": "customer_id",
        "dedup_priority": "monthly_spend",  # keep record with higher spend
        "dedup_priority_direction": "max",
        "id_pattern": r"^CUST-\d{6}$",
        "id_field": "customer_id",
    },
    "financial_transactions": {
        "description": "Financial transaction ledger records",
        "fields": {
            "txn_id":        {"type": "string",  "pattern": r"TXN-[A-Z]{2}-\d{8}"},
            "account_id":    {"type": "string",  "pattern": r"ACC-\d{7}", "required": True},
            "amount":        {"type": "float",   "min": 0.01, "max": 1000000.0},
            "currency":      {"type": "enum",    "values": ["USD", "EUR", "GBP", "JPY", "CAD"]},
            "txn_type":      {"type": "enum",    "values": ["credit", "debit", "transfer", "refund"]},
            "status":        {"type": "enum",    "values": ["pending", "completed", "failed", "reversed"]},
            "txn_date":      {"type": "date",    "pattern": r"\d{4}-\d{2}-\d{2}"},
            "description":   {"type": "string",  "required": False, "max_length": 200},
        },
        "cross_field_rules": [
            {
                "rule_id": "refund_amount",
                "description": "refund transactions must have amount <= 50000",
                "condition": "txn_type == 'refund'",
                "target_field": "amount",
                "target_max": 50000.0,
            },
            {
                "rule_id": "failed_status_amount",
                "description": "failed transactions must have amount > 0",
                "condition": "status == 'failed'",
                "target_field": "amount",
                "target_min": 0.01,
            },
        ],
        "dedup_key": "txn_id",
        "dedup_priority": "txn_date",  # keep the later date (lexicographic)
        "dedup_priority_direction": "max",
        "id_pattern": r"^TXN-[A-Z]{2}-\d{8}$",
        "id_field": "txn_id",
    },
    "sensor_readings": {
        "description": "IoT sensor telemetry readings",
        "fields": {
            "reading_id":    {"type": "string",  "pattern": r"RD-\d{10}"},
            "sensor_id":     {"type": "string",  "pattern": r"SENS-[A-Z]\d{4}", "required": True},
            "temperature":   {"type": "float",   "min": -50.0, "max": 150.0},
            "humidity":      {"type": "float",   "min": 0.0,   "max": 100.0},
            "pressure":      {"type": "float",   "min": 800.0, "max": 1100.0},
            "location":      {"type": "string",  "required": True},
            "unit":          {"type": "enum",    "values": ["celsius", "fahrenheit", "kelvin"]},
            "timestamp":     {"type": "datetime","pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"},
        },
        "cross_field_rules": [
            {
                "rule_id": "fahrenheit_range",
                "description": "If unit=fahrenheit then temperature range is -58 to 302",
                "condition": "unit == 'fahrenheit'",
                "target_field": "temperature",
                "target_min": -58.0,
                "target_max": 302.0,
            },
            {
                "rule_id": "kelvin_min",
                "description": "If unit=kelvin then temperature must be >= 223.15 (absolute zero -50C)",
                "condition": "unit == 'kelvin'",
                "target_field": "temperature",
                "target_min": 223.15,
            },
        ],
        "dedup_key": "reading_id",
        "dedup_priority": "timestamp",  # keep the latest timestamp
        "dedup_priority_direction": "max",
        "id_pattern": r"^RD-\d{10}$",
        "id_field": "reading_id",
    },
    "product_catalog": {
        "description": "E-commerce product catalog entries",
        "fields": {
            "product_id":   {"type": "string",  "pattern": r"PROD-[A-Z]{3}-\d{5}"},
            "sku":          {"type": "string",  "pattern": r"[A-Z]{2}\d{4}[A-Z]{2}", "required": True},
            "name":         {"type": "string",  "required": True},
            "category":     {"type": "enum",    "values": ["electronics", "clothing", "food", "books", "sports", "home"]},
            "price":        {"type": "float",   "min": 0.01, "max": 99999.99},
            "stock_count":  {"type": "integer", "min": 0,    "max": 100000},
            "weight_kg":    {"type": "float",   "min": 0.001,"max": 500.0},
            "is_active":    {"type": "boolean"},
        },
        "cross_field_rules": [
            {
                "rule_id": "active_stock",
                "description": "Active products (is_active=true) must have stock_count >= 0",
                "condition": "is_active == 'true'",
                "target_field": "stock_count",
                "target_min": 0,
            },
            {
                "rule_id": "food_weight",
                "description": "food category items must have weight_kg <= 50",
                "condition": "category == 'food'",
                "target_field": "weight_kg",
                "target_max": 50.0,
            },
        ],
        "dedup_key": "product_id",
        "dedup_priority": "price",  # keep the higher price (more authoritative)
        "dedup_priority_direction": "max",
        "id_pattern": r"^PROD-[A-Z]{3}-\d{5}$",
        "id_field": "product_id",
    },
}

# Bug types injected into pipeline.py
BUG_TYPES = [
    "missing_null_check",
    "wrong_regex",
    "missing_cross_field",
    "wrong_dedup_logic",
    "missing_type_coercion",
]

# ── Sample data generators per domain ────────────────────────────────────────

def _gen_customer_records(rng: SeededRandom, names: NamePool, n: int) -> list[dict]:
    tiers = ["free", "pro", "enterprise"]
    countries = ["US", "CA", "UK", "DE", "FR", "AU", "JP"]
    rows = []
    for i in range(n):
        tier = rng.choice(tiers)
        country = rng.choice(countries)
        # Valid zip for US, non-zip for others
        zip_code = f"{rng.randint(10000, 99999)}" if country == "US" else f"{rng.randint(1000, 9999)}"
        spend = round(rng.uniform(0.0, 5000.0), 2)
        if tier == "enterprise" and spend < 500:
            spend = round(rng.uniform(500.0, 5000.0), 2)
        rows.append({
            "customer_id": f"CUST-{100000 + i:06d}",
            "company_name": f"{names.next()} Corp",
            "email": f"contact{i}@{names.next().lower()}.com",
            "country": country,
            "zip_code": zip_code,
            "account_tier": tier,
            "monthly_spend": str(spend),
            "signup_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        })
    return rows


def _gen_financial_transactions(rng: SeededRandom, n: int) -> list[dict]:
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]
    txn_types = ["credit", "debit", "transfer", "refund"]
    statuses = ["pending", "completed", "failed", "reversed"]
    suffixes = ["AB", "CD", "EF", "GH", "XY", "ZZ", "MN", "PQ"]
    rows = []
    for i in range(n):
        txn_type = rng.choice(txn_types)
        status = rng.choice(statuses)
        amount = round(rng.uniform(1.0, 10000.0), 2)
        if txn_type == "refund" and amount > 50000:
            amount = round(rng.uniform(100.0, 5000.0), 2)
        rows.append({
            "txn_id": f"TXN-{rng.choice(suffixes)}-{10000000 + i:08d}",
            "account_id": f"ACC-{1000000 + rng.randint(0, 999999):07d}",
            "amount": str(amount),
            "currency": rng.choice(currencies),
            "txn_type": txn_type,
            "status": status,
            "txn_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "description": f"Transaction {i} processed",
        })
    return rows


def _gen_sensor_readings(rng: SeededRandom, n: int) -> list[dict]:
    units = ["celsius", "fahrenheit", "kelvin"]
    locations = ["warehouse-A", "server-room-B", "outdoor-C", "lab-D", "plant-E"]
    rows = []
    for i in range(n):
        unit = rng.choice(units)
        if unit == "celsius":
            temp = round(rng.uniform(-40.0, 100.0), 2)
        elif unit == "fahrenheit":
            temp = round(rng.uniform(-40.0, 212.0), 2)
        else:
            temp = round(rng.uniform(233.15, 373.15), 2)
        rows.append({
            "reading_id": f"RD-{1000000000 + i:010d}",
            "sensor_id": f"SENS-{chr(65 + (i % 26))}{1000 + i:04d}",
            "temperature": str(temp),
            "humidity": str(round(rng.uniform(10.0, 95.0), 2)),
            "pressure": str(round(rng.uniform(900.0, 1050.0), 2)),
            "location": rng.choice(locations),
            "unit": unit,
            "timestamp": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}",
        })
    return rows


def _gen_product_catalog(rng: SeededRandom, names: NamePool, n: int) -> list[dict]:
    categories = ["electronics", "clothing", "food", "books", "sports", "home"]
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rows = []
    for i in range(n):
        cat = rng.choice(categories)
        price = round(rng.uniform(1.0, 500.0), 2)
        weight = round(rng.uniform(0.01, 30.0), 3)
        if cat == "food" and weight > 50.0:
            weight = round(rng.uniform(0.1, 5.0), 3)
        rows.append({
            "product_id": f"PROD-{letters[i % 26]}{letters[(i+1) % 26]}{letters[(i+2) % 26]}-{10000 + i:05d}",
            "sku": f"{letters[i % 26]}{letters[(i+3) % 26]}{1000 + i:04d}{letters[(i+5) % 26]}{letters[(i+7) % 26]}",
            "name": f"{names.next()} {cat.title()} Item",
            "category": cat,
            "price": str(price),
            "stock_count": str(rng.randint(0, 500)),
            "weight_kg": str(weight),
            "is_active": rng.choice(["true", "false"]),
        })
    return rows


class Generator(TaskGenerator):
    task_id = "D4_data_pipeline"
    domain = "data"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        names = NamePool(seed, count=60)

        # Pick domain deterministically from seed
        domain_names = list(DOMAINS.keys())
        domain_name = domain_names[seed % len(domain_names)]
        domain = DOMAINS[domain_name]

        # Pick bug types (3 of the 5)
        bug_sample = rng.sample(BUG_TYPES, 3)
        has_missing_null = "missing_null_check" in bug_sample
        has_wrong_regex = "wrong_regex" in bug_sample
        has_missing_cross_field = "missing_cross_field" in bug_sample
        has_wrong_dedup = "wrong_dedup_logic" in bug_sample
        has_missing_coercion = "missing_type_coercion" in bug_sample

        # Generate n clean base rows
        n_rows = rng.randint(18, 30)
        base_rows = self._gen_domain_rows(domain_name, rng, names, n_rows)

        fields = list(domain["fields"].keys())
        id_field = domain["id_field"]
        dedup_key = domain["dedup_key"]
        dedup_priority = domain["dedup_priority"]
        dedup_direction = domain["dedup_priority_direction"]

        # ── Inject faults ──────────────────────────────────────────────────

        # 1. Null/empty field injection (2 rows)
        null_ids = []
        null_candidates = rng.sample(base_rows[:n_rows // 2], 2)
        required_fields = [f for f, spec in domain["fields"].items()
                           if spec.get("required", True) and f != id_field]
        for row in null_candidates:
            field_to_null = rng.choice(required_fields)
            row[field_to_null] = ""
            null_ids.append(row[id_field])

        # 2. Pattern violations (2 rows — bad id format)
        bad_pattern_ids = []
        pattern_candidates = rng.sample(
            [r for r in base_rows if r[id_field] not in null_ids], 2
        )
        for row in pattern_candidates:
            row[id_field] = "INVALID-" + row[id_field]
            bad_pattern_ids.append(row[id_field])

        # 3. Range violations (2 rows)
        range_ids = []
        range_fields = [
            (f, spec) for f, spec in domain["fields"].items()
            if spec["type"] in ("float", "integer") and "min" in spec
        ]
        range_candidates = rng.sample(
            [r for r in base_rows
             if r[id_field] not in null_ids and r[id_field] not in bad_pattern_ids],
            min(2, len([r for r in base_rows
                        if r[id_field] not in null_ids and r[id_field] not in bad_pattern_ids]))
        )
        for row in range_candidates:
            if range_fields:
                rf, rspec = rng.choice(range_fields)
                if rspec["type"] == "float":
                    row[rf] = str(round(rspec["max"] + rng.uniform(10.0, 100.0), 2))
                else:
                    row[rf] = str(rspec["max"] + rng.randint(10, 100))
                range_ids.append(row[id_field])

        # 4. Cross-field violations (inject 2 rows that violate cross-field rules)
        cross_field_ids = []
        cross_rules = domain["cross_field_rules"]
        clean_remaining = [
            r for r in base_rows
            if r[id_field] not in null_ids
            and r[id_field] not in bad_pattern_ids
            and r[id_field] not in range_ids
        ]
        cross_candidates = rng.sample(clean_remaining[:max(2, len(clean_remaining) // 2)],
                                      min(2, len(clean_remaining)))
        for i, row in enumerate(cross_candidates):
            rule = cross_rules[i % len(cross_rules)]
            # Force the condition to be true, then violate the target
            cond_field, cond_value = self._parse_condition(rule["condition"])
            if cond_field in row:
                row[cond_field] = cond_value
            target = rule["target_field"]
            if "target_max" in rule:
                row[target] = str(round(float(rule["target_max"]) + 100.0, 2))
            elif "target_min" in rule:
                val = float(rule.get("target_min", 0))
                row[target] = str(round(val - 50.0, 2))
            elif "target_pattern" in rule:
                row[target] = "BADZIP"
            cross_field_ids.append(row[id_field])

        # 5. Enum violations (1 row)
        enum_ids = []
        enum_fields = [(f, spec) for f, spec in domain["fields"].items()
                       if spec["type"] == "enum"]
        remaining_clean = [
            r for r in base_rows
            if r[id_field] not in null_ids
            and r[id_field] not in bad_pattern_ids
            and r[id_field] not in range_ids
            and r[id_field] not in cross_field_ids
        ]
        if enum_fields and remaining_clean:
            enum_row = rng.choice(remaining_clean)
            ef, espec = rng.choice(enum_fields)
            enum_row[ef] = "INVALID_ENUM_VALUE"
            enum_ids.append(enum_row[id_field])

        # 6. Duplicate rows (2 pairs — each id appears twice with different priority value)
        dup_pairs = []  # (id, winner_priority_val, loser_priority_val)
        dup_source_rows = [
            r for r in base_rows
            if r[id_field] not in null_ids
            and r[id_field] not in bad_pattern_ids
            and r[id_field] not in range_ids
            and r[id_field] not in cross_field_ids
            and r[id_field] not in enum_ids
        ]
        dup_candidates = rng.sample(dup_source_rows[:max(2, len(dup_source_rows) // 2)],
                                    min(2, len(dup_source_rows)))
        duplicate_rows = []
        for row in dup_candidates:
            orig_prio = self._parse_priority(row.get(dedup_priority, "0"))
            new_prio_val = self._new_priority(rng, orig_prio, dedup_direction, dedup_priority)
            dup_row = dict(row)
            dup_row[dedup_priority] = new_prio_val
            # Determine winner
            if dedup_direction == "max":
                winner = max(self._parse_priority(new_prio_val), orig_prio)
                winner_str = new_prio_val if self._parse_priority(new_prio_val) == winner else row[dedup_priority]
            else:
                winner = min(self._parse_priority(new_prio_val), orig_prio)
                winner_str = new_prio_val if self._parse_priority(new_prio_val) == winner else row[dedup_priority]
            dup_pairs.append({
                "id": row[id_field],
                "winner_priority": winner_str,
            })
            duplicate_rows.append(dup_row)

        # Assemble full input
        all_rows = base_rows + duplicate_rows
        rng.shuffle(all_rows)

        # ── Compute expected output ────────────────────────────────────────
        # Invalid IDs = bad_pattern_ids + null_ids (null in required field) + range_ids + cross_field_ids + enum_ids
        all_invalid_ids = set(bad_pattern_ids) | set(null_ids) | set(range_ids) | set(cross_field_ids) | set(enum_ids)

        # Step 1: Remove invalid records
        valid_rows = [r for r in all_rows if r[id_field] not in all_invalid_ids]

        # Step 2: Dedup by dedup_key — keep winner
        by_key: dict[str, dict] = {}
        for row in valid_rows:
            k = row[id_field]
            if k not in by_key:
                by_key[k] = row.copy()
            else:
                existing_prio = self._parse_priority(by_key[k].get(dedup_priority, "0"))
                new_prio = self._parse_priority(row.get(dedup_priority, "0"))
                if dedup_direction == "max":
                    if new_prio > existing_prio:
                        by_key[k] = row.copy()
                else:
                    if new_prio < existing_prio:
                        by_key[k] = row.copy()

        deduped = list(by_key.values())

        # Step 3: Sort by id_field
        deduped.sort(key=lambda r: r[id_field])

        expected_row_count = len(deduped)

        # Build spot checks
        spot_ids = [r[id_field] for r in deduped[:3]] + ([deduped[-1][id_field]] if deduped else [])
        spot_ids = list(dict.fromkeys(spot_ids))
        spot_checks = {sid: {dedup_priority: deduped[[r[id_field] for r in deduped].index(sid)][dedup_priority]}
                       for sid in spot_ids if sid in [r[id_field] for r in deduped]}

        expected = {
            "domain": domain_name,
            "id_field": id_field,
            "dedup_key": dedup_key,
            "dedup_priority": dedup_priority,
            "dedup_priority_direction": dedup_direction,
            "row_count": expected_row_count,
            "columns": fields,
            "invalid_ids": sorted(all_invalid_ids),
            "null_ids": null_ids,
            "bad_pattern_ids": bad_pattern_ids,
            "range_ids": range_ids,
            "cross_field_ids": cross_field_ids,
            "enum_ids": enum_ids,
            "dup_winner_priorities": {p["id"]: p["winner_priority"] for p in dup_pairs},
            "spot_checks": spot_checks,
            "cross_field_rules": cross_rules,
            "bug_types_injected": bug_sample,
        }

        # ── Generate files ─────────────────────────────────────────────────
        csv_content = self._to_csv(all_rows, fields)
        rules_json = self._generate_partial_rules(domain, domain_name)
        pipeline_py = self._generate_buggy_pipeline(
            domain_name, domain, fields, id_field, dedup_key, dedup_priority, dedup_direction,
            has_missing_null, has_wrong_regex, has_missing_cross_field,
            has_wrong_dedup, has_missing_coercion,
        )
        spec_md = self._generate_spec(domain_name, domain, fields, id_field,
                                      dedup_key, dedup_priority, dedup_direction)
        brief_md = self._generate_brief(domain_name, domain)

        workspace_files = {
            "pipeline.py": pipeline_py,
            "data/input.csv": csv_content,
            "config/rules.json": rules_json,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── Domain row generators ─────────────────────────────────────────────

    def _gen_domain_rows(self, domain_name: str, rng: SeededRandom,
                         names: NamePool, n: int) -> list[dict]:
        if domain_name == "customer_records":
            return _gen_customer_records(rng, names, n)
        elif domain_name == "financial_transactions":
            return _gen_financial_transactions(rng, n)
        elif domain_name == "sensor_readings":
            return _gen_sensor_readings(rng, n)
        else:
            return _gen_product_catalog(rng, names, n)

    # ── Priority helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_priority(val: str) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            # Lexicographic for date/datetime strings — convert to comparable float
            # by treating as string ordinal sum
            return sum(ord(c) for c in str(val))

    @staticmethod
    def _new_priority(rng: SeededRandom, orig: float, direction: str, field: str) -> str:
        if field in ("txn_date", "timestamp", "signup_date"):
            # Generate a different date string (higher lexicographic)
            if direction == "max":
                return "2025-01-15"
            else:
                return "2023-06-01"
        if direction == "max":
            new_val = round(orig + rng.uniform(50.0, 500.0), 2)
        else:
            new_val = round(max(0.01, orig - rng.uniform(10.0, 100.0)), 2)
        return str(new_val)

    @staticmethod
    def _parse_condition(condition: str) -> tuple[str, str]:
        """Parse 'field == value' -> (field, value)."""
        parts = condition.split("==")
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip().strip("'\"")
        return ("", "")

    # ── File generators ───────────────────────────────────────────────────

    @staticmethod
    def _to_csv(rows: list[dict], cols: list[str]) -> str:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue()

    @staticmethod
    def _generate_partial_rules(domain: dict, domain_name: str) -> str:
        """
        Partial rules visible to the agent — omits cross-field constraints
        and dedup priority direction (those are only in spec.md).
        """
        partial = {
            "domain": domain_name,
            "note": "This is a partial ruleset. The full specification contains additional cross-field constraints and deduplication priority rules.",
            "fields": {},
            "dedup_key": domain["dedup_key"],
        }
        for field_name, spec in domain["fields"].items():
            entry = {"type": spec["type"]}
            if "required" in spec:
                entry["required"] = spec["required"]
            if "values" in spec:
                entry["values"] = spec["values"]
            if "min" in spec:
                entry["min"] = spec["min"]
            if "max" in spec:
                entry["max"] = spec["max"]
            if "pattern" in spec:
                # Slightly obscured pattern — missing anchors — to make it a real challenge
                entry["pattern_hint"] = spec["pattern"]
            partial["fields"][field_name] = entry
        return json.dumps(partial, indent=2)

    def _generate_buggy_pipeline(
        self,
        domain_name: str,
        domain: dict,
        fields: list[str],
        id_field: str,
        dedup_key: str,
        dedup_priority: str,
        dedup_direction: str,
        has_missing_null: bool,
        has_wrong_regex: bool,
        has_missing_cross_field: bool,
        has_wrong_dedup: bool,
        has_missing_coercion: bool,
    ) -> str:
        # Build enum validation snippet
        enum_checks = []
        for fname, spec in domain["fields"].items():
            if spec["type"] == "enum":
                enum_checks.append(
                    f'    if row.get("{fname}") not in {spec["values"]}:\n'
                    f'        errors.append(f\'{{row["{id_field}"]}} invalid {fname}: {{row.get("{fname}")}}\')' )
        enum_block = "\n".join(enum_checks) if enum_checks else "    pass  # no enum checks"

        # Build range validation snippet
        range_checks = []
        for fname, spec in domain["fields"].items():
            if spec["type"] in ("float", "integer") and "min" in spec:
                coerce_fn = "float" if spec["type"] == "float" else "int"
                if has_missing_coercion:
                    # Bug: catches ValueError/TypeError silently — out-of-range values
                    # slip through as valid because the exception swallows the check
                    range_checks.append(
                        f'    # BUG: missing type coercion — exception silently swallowed, range not checked\n'
                        f'    try:\n'
                        f'        val_{fname} = row.get("{fname}", "")\n'
                        f'        if not ({spec["min"]} <= val_{fname} <= {spec["max"]}):\n'
                        f'            errors.append(f\'{{row["{id_field}"]}} {fname} out of range\')\n'
                        f'    except (ValueError, TypeError):\n'
                        f'        pass  # BUG: should flag as error, not silently pass'
                    )
                else:
                    range_checks.append(
                        f'    try:\n'
                        f'        val_{fname} = {coerce_fn}(row.get("{fname}", 0))\n'
                        f'        if not ({spec["min"]} <= val_{fname} <= {spec["max"]}):\n'
                        f'            errors.append(f\'{{row["{id_field}"]}} {fname} out of range: {{val_{fname}}}\')\n'
                        f'    except (ValueError, TypeError):\n'
                        f'        errors.append(f\'{{row["{id_field}"]}} {fname} not a number\')'
                    )
        range_block = "\n".join(range_checks) if range_checks else "    pass  # no range checks"

        # Build id pattern check
        id_pattern = domain["id_pattern"]
        if has_wrong_regex:
            # Bug: wrong pattern (missing anchors / wrong character class)
            buggy_pattern = id_pattern.replace(r"^\d", r"\d").replace(r"\d$", r"\d").replace("^", "").replace("$", "")
            id_check = (
                f'    # BUG: wrong regex pattern (missing anchors)\n'
                f'    ID_PATTERN = r"{buggy_pattern}"\n'
                f'    if not re.search(ID_PATTERN, row.get("{id_field}", "")):\n'
                f'        errors.append(f\'{{row["{id_field}"]}} invalid {id_field} format\')'
            )
        else:
            id_check = (
                f'    ID_PATTERN = r"{id_pattern}"\n'
                f'    if not re.fullmatch(ID_PATTERN, row.get("{id_field}", "")):\n'
                f'        errors.append(f\'{{row["{id_field}"]}} invalid {id_field} format\')'
            )

        # Build null check
        required_fields = [f for f, spec in domain["fields"].items()
                           if spec.get("required", True)]
        if has_missing_null:
            null_check = (
                f'    # BUG: only checks for None, misses empty string\n'
                f'    for req_field in {required_fields!r}:\n'
                f'        if row.get(req_field) is None:\n'
                f'            errors.append(f\'{{row["{id_field}"]}} missing required field: {{req_field}}\')'
            )
        else:
            null_check = (
                f'    for req_field in {required_fields!r}:\n'
                f'        if not row.get(req_field):\n'
                f'            errors.append(f\'{{row["{id_field}"]}} missing required field: {{req_field}}\')'
            )

        # Build cross-field check
        cross_rules = domain["cross_field_rules"]
        if has_missing_cross_field:
            cross_block = "    # BUG: cross-field validation not implemented\n    pass"
        else:
            cross_lines = []
            for rule in cross_rules:
                cond_field, cond_val = self._parse_condition(rule["condition"])
                target = rule["target_field"]
                cross_lines.append(f'    # Rule: {rule["rule_id"]} — {rule["description"]}')
                cross_lines.append(f'    if row.get("{cond_field}") == "{cond_val}":')
                if "target_pattern" in rule:
                    cross_lines.append(f'        if not re.fullmatch(r"{rule["target_pattern"]}", str(row.get("{target}", ""))):\n'
                                       f'            errors.append(f\'{{row["{id_field}"]}} cross-field rule {rule["rule_id"]} violated\')')
                elif "target_max" in rule:
                    cross_lines.append(f'        try:\n'
                                       f'            if float(row.get("{target}", 0)) > {rule["target_max"]}:\n'
                                       f'                errors.append(f\'{{row["{id_field}"]}} cross-field rule {rule["rule_id"]} violated\')\n'
                                       f'        except (ValueError, TypeError): pass')
                elif "target_min" in rule:
                    cross_lines.append(f'        try:\n'
                                       f'            if float(row.get("{target}", 0)) < {rule["target_min"]}:\n'
                                       f'                errors.append(f\'{{row["{id_field}"]}} cross-field rule {rule["rule_id"]} violated\')\n'
                                       f'        except (ValueError, TypeError): pass')
            cross_block = "\n".join(cross_lines)

        # Build dedup logic — the full loop is self-contained in dedup_block
        if has_wrong_dedup:
            dedup_block = (
                f'    # BUG: keeps first occurrence instead of highest {dedup_priority}\n'
                f'    seen_ids = set()\n'
                f'    for row in valid_rows:\n'
                f'        if row["{dedup_key}"] not in seen_ids:\n'
                f'            seen_ids.add(row["{dedup_key}"])\n'
                f'            deduped.append(row)'
            )
        else:
            if dedup_direction == "max":
                compare_op = ">"
            else:
                compare_op = "<"
            dedup_block = (
                f'    seen_keys = {{}}\n'
                f'    for row in valid_rows:\n'
                f'        key = row["{dedup_key}"]\n'
                f'        if key not in seen_keys:\n'
                f'            seen_keys[key] = row\n'
                f'        else:\n'
                f'            # Keep {dedup_direction} {dedup_priority}\n'
                f'            existing_prio = seen_keys[key].get("{dedup_priority}", "")\n'
                f'            new_prio = row.get("{dedup_priority}", "")\n'
                f'            try:\n'
                f'                if float(new_prio) {compare_op} float(existing_prio):\n'
                f'                    seen_keys[key] = row\n'
                f'            except (ValueError, TypeError):\n'
                f'                if str(new_prio) {compare_op} str(existing_prio):\n'
                f'                    seen_keys[key] = row\n'
                f'    deduped = list(seen_keys.values())'
            )
        dedup_collect = ""  # loop+collect both inside dedup_block now

        fields_repr = repr(fields)
        return f'''"""
Data validation pipeline for domain: {domain_name}.

Run with: python pipeline.py

This pipeline reads data/input.csv, validates each record against the rules
in config/rules.json (partial), and writes valid records to data/output/valid.csv
and invalid records (with error reasons) to data/output/invalid.csv.

BUGS to fix:
  - See inline BUG comments for specific issues.
  - The full validation ruleset is in the task spec; config/rules.json is partial.
"""
import csv
import json
import os
import re

INPUT_PATH = "data/input.csv"
OUTPUT_VALID = "data/output/valid.csv"
OUTPUT_INVALID = "data/output/invalid.csv"
RULES_PATH = "config/rules.json"

FIELDS = {fields_repr}


def load_rules(path: str = RULES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_row(row: dict, rules: dict) -> list[str]:
    """Return list of error strings; empty list means valid."""
    errors = []

    # ── Null / required field check ───────────────────────────────────────
{null_check}

    # ── ID pattern check ──────────────────────────────────────────────────
{id_check}

    # ── Range checks ──────────────────────────────────────────────────────
{range_block}

    # ── Enum checks ───────────────────────────────────────────────────────
{enum_block}

    # ── Cross-field constraint checks ─────────────────────────────────────
{cross_block}

    return errors


def run():
    rules = load_rules()
    os.makedirs("data/output", exist_ok=True)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    # ── Validation pass ───────────────────────────────────────────────────
    valid_rows = []
    invalid_rows = []
    for row in all_rows:
        errs = validate_row(row, rules)
        if errs:
            row["_errors"] = "; ".join(errs)
            invalid_rows.append(row)
        else:
            valid_rows.append(row)

    # ── Deduplication (applied to valid rows only) ────────────────────────
    deduped = []
{dedup_block}

    # ── Sort output by {id_field} ─────────────────────────────────────────
    deduped.sort(key=lambda r: r["{id_field}"])

    # ── Write outputs ─────────────────────────────────────────────────────
    with open(OUTPUT_VALID, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(deduped)

    with open(OUTPUT_INVALID, "w", encoding="utf-8", newline="") as f:
        invalid_fields = FIELDS + ["_errors"]
        writer = csv.DictWriter(f, fieldnames=invalid_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(invalid_rows)

    print(f"Valid records:   {{len(deduped)}}")
    print(f"Invalid records: {{len(invalid_rows)}}")
    print(f"Total processed: {{len(all_rows)}}")


if __name__ == "__main__":
    run()
'''

    def _generate_spec(
        self,
        domain_name: str,
        domain: dict,
        fields: list[str],
        id_field: str,
        dedup_key: str,
        dedup_priority: str,
        dedup_direction: str,
    ) -> str:
        # Full field rules table
        field_rows = []
        for fname, spec in domain["fields"].items():
            ftype = spec["type"]
            constraints = []
            if spec.get("required", True):
                constraints.append("required")
            if "pattern" in spec:
                constraints.append(f'pattern: `{spec["pattern"]}`')
            if "values" in spec:
                constraints.append(f'enum: {spec["values"]}')
            if "min" in spec:
                constraints.append(f'min: {spec["min"]}')
            if "max" in spec:
                constraints.append(f'max: {spec["max"]}')
            if "max_length" in spec:
                constraints.append(f'max_length: {spec["max_length"]}')
            field_rows.append(f"| `{fname}` | {ftype} | {', '.join(constraints) or 'none'} |")
        field_table = "\n".join(field_rows)

        # Cross-field rules section
        cross_sections = []
        for rule in domain["cross_field_rules"]:
            constraints = []
            if "target_pattern" in rule:
                constraints.append(f'`{rule["target_field"]}` must match `{rule["target_pattern"]}`')
            if "target_max" in rule:
                constraints.append(f'`{rule["target_field"]}` <= {rule["target_max"]}')
            if "target_min" in rule:
                constraints.append(f'`{rule["target_field"]}` >= {rule["target_min"]}')
            cross_sections.append(
                f'- **Rule `{rule["rule_id"]}`**: {rule["description"]}\n'
                f'  - Condition: `{rule["condition"]}`\n'
                f'  - Constraint: {", ".join(constraints)}'
            )
        cross_block = "\n".join(cross_sections)

        dir_word = "highest" if dedup_direction == "max" else "lowest"

        return f"""# D4: Data Validation Pipeline — {domain_name.replace("_", " ").title()}

## Goal
Fix `pipeline.py` so it correctly validates, deduplicates, and outputs the
`{domain_name}` dataset. The pipeline reads `data/input.csv` and must produce:
- `data/output/valid.csv` — records passing ALL validation rules
- `data/output/invalid.csv` — records failing any rule, with `_errors` column

## Domain
{domain["description"]}

## Input Schema

| Field | Type | Constraints |
|-------|------|-------------|
{field_table}

## Complete Validation Ruleset (10+ rules)

### 1. Null / Required Field Check
Every field marked **required** must be non-empty (not `""` and not `None`).
Rejecting only `None` while allowing `""` is a bug.

### 2. ID Format Check
`{id_field}` must match the regex `{domain["id_pattern"]}` exactly (full match, anchored).
Using `re.search()` without anchors is a bug — it allows `INVALID-{id_field[0:4]}...` to pass.

### 3. Range Validation
All numeric fields must be coerced to the correct type before range comparison.
Comparing a raw string to a numeric bound is a bug.
{chr(10).join(f"- `{fn}`: [{spec.get('min', 'N/A')}, {spec.get('max', 'N/A')}]" for fn, spec in domain["fields"].items() if "min" in spec)}

### 4. Enum Validation
Fields with enumerated values must reject any value not in the allowed set:
{chr(10).join(f"- `{fn}`: {spec['values']}" for fn, spec in domain["fields"].items() if spec['type'] == 'enum')}

### 5. Cross-Field Constraints (NOT in config/rules.json — spec only)

{cross_block}

### 6. Deduplication Rules
- **Dedup key**: `{dedup_key}` — records with the same key are duplicates.
- **Priority field**: `{dedup_priority}` — keep the record with the {dir_word} `{dedup_priority}`.
- **Direction**: `{dedup_direction}` — keeping first occurrence is a bug.
- Apply deduplication **after** validation (only among valid records).

### 7. Output Requirements
- `data/output/valid.csv`: deduplicated valid records, sorted ascending by `{id_field}`.
- `data/output/invalid.csv`: all invalid records (pre-dedup) with `_errors` column containing semicolon-separated error messages.
- Column order in both outputs must match input schema exactly: `{fields}`.

### 8. Type Coercion
Before any numeric comparison, cast the field to the correct Python type (`int` or `float`).
Wrap in try/except and treat non-numeric values as validation errors.

### 9. Pattern Matching
Use `re.fullmatch()` (not `re.search()` or `re.match()`) for all pattern checks.

### 10. Error Accumulation
A single record may fail multiple rules. Collect ALL errors before deciding invalid.
Do not short-circuit after the first error.

## Hard Requirements
1. `python pipeline.py` exits with code 0 and produces both output files.
2. No valid records appear in `invalid.csv` (false positives).
3. No invalid records appear in `valid.csv` (false negatives).
4. Cross-field constraints are enforced (these are NOT in `config/rules.json`).
5. Deduplication keeps the {dir_word} `{dedup_priority}` record.
6. Output files are UTF-8 with Unix line endings.
7. All 10+ rules must be correctly implemented.

## Deliverables
- Fixed `pipeline.py` in workspace.
- Both output files generated on `python pipeline.py`.
- Verifier must confirm all rules and produce attestation.
"""

    def _generate_brief(self, domain_name: str, domain: dict) -> str:
        return f"""# D4: Data Validation Pipeline (Brief)

The `{domain_name}` data pipeline is producing invalid records.
Fix the validation logic in `pipeline.py`.

The Planner has the complete validation ruleset including cross-field constraints
and deduplication priority rules. `config/rules.json` contains only a partial ruleset.

Run: `python pipeline.py`
Input: `data/input.csv`
Output: `data/output/valid.csv` and `data/output/invalid.csv`
"""
