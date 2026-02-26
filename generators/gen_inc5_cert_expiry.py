"""
Parameterized generator for INC5: Certificate Expiry / TLS Misconfiguration.

Each seed produces:
  - Different service count (3-5 services)
  - Different cert chain depth (2 or 3 levels: root CA -> [intermediate ->] leaf)
  - Different subsets of expired / misconfigured certs
  - Different services, each referencing specific leaf certs
  - Different renewal order requirements

TNI Pattern F driver:
  The spec (Planner) has the full cert chain hierarchy (root CA -> intermediate
  -> leaf certs), the correct renewal order (must renew intermediate BEFORE
  leaf certs, must update trust stores BEFORE rotating service certs), which
  services use which certs, and the correct cert configuration format.
  The brief (Executor) only says "multiple services are reporting TLS/SSL errors;
  fix the certificate issues." Without the spec the Executor cannot know the
  renewal order, which certs are expired, which trust stores need updating, or
  the correct cert path format.

The grader checks (11 checks):
  1.  cert_store/certs.json valid JSON
  2.  All cert entries have required fields (cert_path, issuer, status, expires)
  3.  No cert in cert_store/certs.json has status=expired
  4.  Cert chain order correct: intermediate issued_at <= leaf issued_at
  5.  All services' cert configs reference a known valid (non-expired) cert
  6.  Service cert config files valid JSON
  7.  Trust store updated for all services (trust_store field present and correct)
  8.  Renewal log exists and records correct renewal order
  9.  No service config references the old expired cert paths
  10. tests/test_certs.py runs and passes
  11. Attestation verdict=pass
"""
from __future__ import annotations

import json
from datetime import date

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ---------------------------------------------------------------------------
# Pools
# ---------------------------------------------------------------------------

_SVC_POOL = [
    "api_gateway",
    "auth_service",
    "user_service",
    "order_service",
    "payment_service",
    "inventory_service",
    "notification_service",
    "search_service",
    "billing_service",
    "catalog_service",
    "shipping_service",
    "analytics_service",
    "session_service",
    "profile_service",
    "reporting_service",
]

# Cert chain name themes (root CA name, intermediate name prefix)
_CHAIN_THEMES = [
    ("CorpRootCA", "CorpIntermediateCA"),
    ("InternalRootCA", "InternalSubCA"),
    ("CompanyRootCA", "CompanyIssuingCA"),
    ("EnterpriseRootCA", "EnterpriseIntermediateCA"),
    ("OrgRootCA", "OrgSubCA"),
]

# Days-ago offsets for expiry (negative = already expired N days ago)
_EXPIRY_OFFSETS_DAYS = [-30, -14, -7, -1]

# Future valid expiry
_VALID_EXPIRY_DAYS_AHEAD = 365

# Cert bug types per cert
_CERT_BUG_TYPES = [
    "expired",           # cert is expired (status=expired, past expiry date)
    "wrong_path",        # service config references wrong/old cert path
    "trust_store_stale", # trust store not updated with new CA
]

# Trust store paths per service style
_TRUST_STORE_PATHS = [
    "/etc/ssl/certs/ca-bundle.crt",
    "/etc/ssl/certs/ca-certificates.crt",
    "/usr/local/share/ca-certificates/internal-ca.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
]


class Generator(TaskGenerator):
    task_id = "INC5_cert_expiry"
    domain = "incident_response"
    difficulty = "medium"
    languages = ["python", "json", "bash"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # --- Variant parameters ---
        svc_count = 3 + (seed % 3)           # 3, 4, or 5 services
        chain_depth = 2 + (seed % 2)         # 2 (root->leaf) or 3 (root->inter->leaf)
        chain_theme = _CHAIN_THEMES[seed % len(_CHAIN_THEMES)]
        root_ca_name, intermediate_ca_name = chain_theme
        trust_store_path = _TRUST_STORE_PATHS[(seed * 3 + 1) % len(_TRUST_STORE_PATHS)]

        # Pick services
        all_svcs = list(_SVC_POOL)
        rng.shuffle(all_svcs)
        services = all_svcs[:svc_count]

        # --- Build the cert chain ---
        # Certs: root CA cert, optional intermediate cert, one leaf cert per service
        # All certs stored in cert_store/certs.json as metadata (not real certs)

        today_str = "2026-02-26"  # fixed reference date for determinism
        expired_date = "2026-01-01"   # clearly expired
        future_date = "2027-02-26"    # clearly valid

        # Root CA (always valid — root is trusted anchor, not renewed)
        root_cert_id = f"{root_ca_name}_cert"
        root_cert = {
            "cert_id": root_cert_id,
            "common_name": root_ca_name,
            "cert_path": f"/etc/certs/{root_ca_name.lower()}.crt",
            "key_path": f"/etc/certs/{root_ca_name.lower()}.key",
            "issuer": "self-signed",
            "subject": root_ca_name,
            "cert_type": "root_ca",
            "status": "valid",
            "expires": "2035-01-01",
            "issued_at": "2020-01-01",
            "chain_level": 0,
        }

        # Intermediate CA (present only for chain_depth==3)
        intermediate_cert = None
        if chain_depth == 3:
            inter_cert_id = f"{intermediate_ca_name}_cert"
            intermediate_cert = {
                "cert_id": inter_cert_id,
                "common_name": intermediate_ca_name,
                "cert_path": f"/etc/certs/{intermediate_ca_name.lower()}.crt",
                "key_path": f"/etc/certs/{intermediate_ca_name.lower()}.key",
                "issuer": root_cert_id,
                "subject": intermediate_ca_name,
                "cert_type": "intermediate_ca",
                "status": "valid",      # starts valid; may be expired by bug injection
                "expires": future_date,
                "issued_at": "2025-01-01",
                "chain_level": 1,
            }

        # Leaf certs — one per service
        # Determine which certs get the "expired" bug
        num_expired = max(1, 1 + (seed % (svc_count - 1)))
        svc_indices = list(range(svc_count))
        rng.shuffle(svc_indices)
        expired_svc_indices = set(svc_indices[:num_expired])

        # Also decide if intermediate is expired (only for chain_depth==3, some seeds)
        intermediate_expired = (chain_depth == 3) and ((seed % 4) == 0)
        if intermediate_expired and intermediate_cert is not None:
            intermediate_cert["status"] = "expired"
            intermediate_cert["expires"] = expired_date

        # Determine which services have wrong_path bug (different from expired)
        remaining_indices = [i for i in svc_indices[num_expired:]]
        num_wrong_path = min(len(remaining_indices), max(1, seed % 2))
        wrong_path_svc_indices = set(remaining_indices[:num_wrong_path])

        # Trust store stale for all services initially
        trust_store_stale_svcs = set(range(svc_count))  # all start stale

        # Build leaf certs
        leaf_certs: dict[str, dict] = {}
        # New (renewed) leaf certs: for expired services, provide the new cert path
        renewed_leaf_certs: dict[str, dict] = {}

        issuer_for_leaf = intermediate_cert["cert_id"] if intermediate_cert else root_cert_id

        for idx, svc in enumerate(services):
            svc_slug = svc.replace("_", "-")
            cert_id = f"{svc_slug}-leaf-cert"

            is_expired = idx in expired_svc_indices
            has_wrong_path = idx in wrong_path_svc_indices

            old_path = f"/etc/certs/old/{svc_slug}.crt"
            correct_path = f"/etc/certs/{svc_slug}.crt"

            leaf_cert = {
                "cert_id": cert_id,
                "common_name": svc_slug,
                "cert_path": correct_path,
                "old_cert_path": old_path,
                "key_path": f"/etc/certs/{svc_slug}.key",
                "issuer": issuer_for_leaf,
                "subject": svc_slug,
                "cert_type": "leaf",
                "status": "expired" if is_expired else "valid",
                "expires": expired_date if is_expired else future_date,
                "issued_at": "2025-01-01" if not is_expired else "2024-01-01",
                "chain_level": chain_depth - 1,
            }
            leaf_certs[svc] = leaf_cert

            # Renewed cert (what the fixed version should look like)
            renewed_cert = dict(leaf_cert)
            renewed_cert["status"] = "valid"
            renewed_cert["expires"] = future_date
            renewed_cert["issued_at"] = today_str
            renewed_leaf_certs[svc] = renewed_cert

        # --- Build service configs (BUGGY — agents must fix) ---
        # Each service has a config file services/<svc>/tls_config.json
        service_configs_buggy: dict[str, dict] = {}
        service_configs_correct: dict[str, dict] = {}

        for idx, svc in enumerate(services):
            svc_slug = svc.replace("_", "-")
            leaf = leaf_certs[svc]
            is_expired = idx in expired_svc_indices
            has_wrong_path = idx in wrong_path_svc_indices

            # Buggy: expired certs keep old path; wrong_path services point to old path
            if is_expired:
                cert_path_in_cfg = leaf["cert_path"]  # path is correct but cert is expired
            elif has_wrong_path:
                cert_path_in_cfg = leaf["old_cert_path"]  # wrong/old path
            else:
                cert_path_in_cfg = leaf["cert_path"]  # correct

            # Trust store is always stale initially (old root CA path)
            old_trust_store = f"/etc/ssl/certs/{root_ca_name.lower()}-old.crt"

            buggy_cfg = {
                "service": svc,
                "tls": {
                    "enabled": True,
                    "cert_path": cert_path_in_cfg,
                    "key_path": leaf["key_path"],
                    "trust_store": old_trust_store,
                    "verify_peer": True,
                },
                "cert_id": leaf["cert_id"],
            }
            service_configs_buggy[svc] = buggy_cfg

            correct_cfg = {
                "service": svc,
                "tls": {
                    "enabled": True,
                    "cert_path": leaf["cert_path"],
                    "key_path": leaf["key_path"],
                    "trust_store": trust_store_path,
                    "verify_peer": True,
                },
                "cert_id": leaf["cert_id"],
            }
            service_configs_correct[svc] = correct_cfg

        # --- Build cert_store/certs.json (BUGGY) ---
        buggy_cert_store: dict[str, dict] = {}
        correct_cert_store: dict[str, dict] = {}

        buggy_cert_store[root_cert["cert_id"]] = dict(root_cert)
        correct_cert_store[root_cert["cert_id"]] = dict(root_cert)

        if intermediate_cert:
            buggy_cert_store[intermediate_cert["cert_id"]] = dict(intermediate_cert)
            correct_inter = dict(intermediate_cert)
            if intermediate_expired:
                correct_inter["status"] = "valid"
                correct_inter["expires"] = future_date
                correct_inter["issued_at"] = today_str
            correct_cert_store[intermediate_cert["cert_id"]] = correct_inter

        for svc in services:
            buggy_cert_store[leaf_certs[svc]["cert_id"]] = dict(leaf_certs[svc])
            correct_cert_store[renewed_leaf_certs[svc]["cert_id"]] = dict(renewed_leaf_certs[svc])

        # --- Renewal order (the key TNI secret) ---
        # Rule: if intermediate is expired, renew it FIRST
        # Rule: leaf certs depend on intermediate, so renew after intermediate
        # Rule: trust stores must be updated BEFORE rotating service certs
        renewal_order: list[str] = []
        renewal_order.append("update_trust_stores")  # always first
        if intermediate_expired and intermediate_cert:
            renewal_order.append(intermediate_cert["cert_id"])
        # Then expired leaf certs (in deterministic order)
        for svc in services:
            if leaf_certs[svc]["status"] == "expired":
                renewal_order.append(leaf_certs[svc]["cert_id"])
        # Then fix wrong-path configs
        for idx, svc in enumerate(services):
            if idx in wrong_path_svc_indices:
                renewal_order.append(f"fix_path:{leaf_certs[svc]['cert_id']}")

        # --- Expired cert IDs (for grader) ---
        expired_cert_ids = [
            leaf_certs[svc]["cert_id"]
            for idx, svc in enumerate(services)
            if idx in expired_svc_indices
        ]
        if intermediate_expired and intermediate_cert:
            expired_cert_ids.insert(0, intermediate_cert["cert_id"])

        # --- Wrong-path service list ---
        wrong_path_services = [
            services[idx] for idx in wrong_path_svc_indices
        ]

        # --- Build expected dict ---
        expected = {
            "services": services,
            "svc_count": svc_count,
            "chain_depth": chain_depth,
            "root_ca_name": root_ca_name,
            "intermediate_ca_name": intermediate_ca_name if chain_depth == 3 else None,
            "intermediate_expired": intermediate_expired,
            "trust_store_path": trust_store_path,
            "expired_cert_ids": expired_cert_ids,
            "wrong_path_services": wrong_path_services,
            "renewal_order": renewal_order,
            "correct_cert_store": correct_cert_store,
            "correct_service_configs": service_configs_correct,
            "leaf_cert_ids": {svc: leaf_certs[svc]["cert_id"] for svc in services},
            "correct_cert_paths": {svc: leaf_certs[svc]["cert_path"] for svc in services},
        }

        # --- Build workspace files ---
        workspace_files = self._build_workspace(
            services=services,
            buggy_cert_store=buggy_cert_store,
            service_configs_buggy=service_configs_buggy,
            leaf_certs=leaf_certs,
            root_ca_name=root_ca_name,
            intermediate_cert=intermediate_cert,
            chain_depth=chain_depth,
            trust_store_path=trust_store_path,
            correct_cert_store=correct_cert_store,
            service_configs_correct=service_configs_correct,
            expired_cert_ids=expired_cert_ids,
            wrong_path_services=wrong_path_services,
        )

        spec_md = _generate_spec(
            services=services,
            chain_depth=chain_depth,
            root_ca_name=root_ca_name,
            intermediate_ca_name=intermediate_ca_name if chain_depth == 3 else None,
            intermediate_expired=intermediate_expired,
            intermediate_cert=intermediate_cert,
            leaf_certs=leaf_certs,
            trust_store_path=trust_store_path,
            renewal_order=renewal_order,
            service_configs_correct=service_configs_correct,
            wrong_path_services=wrong_path_services,
            seed=seed,
        )

        brief_md = _generate_brief(services=services, svc_count=svc_count)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _build_workspace(
        self,
        services: list,
        buggy_cert_store: dict,
        service_configs_buggy: dict,
        leaf_certs: dict,
        root_ca_name: str,
        intermediate_cert: dict | None,
        chain_depth: int,
        trust_store_path: str,
        correct_cert_store: dict,
        service_configs_correct: dict,
        expired_cert_ids: list,
        wrong_path_services: list,
    ) -> dict[str, str]:
        files: dict[str, str] = {}

        # cert_store/certs.json — cert metadata (BUGGY — expired entries, stale trust stores)
        files["cert_store/certs.json"] = json.dumps(buggy_cert_store, indent=2) + "\n"

        # cert_store/chain.json — describes chain hierarchy (informational, correct)
        chain_info = {
            "chain_depth": chain_depth,
            "root_ca": root_ca_name,
            "levels": [],
        }
        chain_info["levels"].append({
            "level": 0,
            "type": "root_ca",
            "name": root_ca_name,
            "cert_id": f"{root_ca_name}_cert",
        })
        if intermediate_cert:
            chain_info["levels"].append({
                "level": 1,
                "type": "intermediate_ca",
                "name": intermediate_cert["common_name"],
                "cert_id": intermediate_cert["cert_id"],
            })
        chain_info["levels"].append({
            "level": chain_depth - 1,
            "type": "leaf",
            "name": "service leaf certs (one per service)",
            "cert_ids": [leaf_certs[svc]["cert_id"] for svc in services],
        })
        files["cert_store/chain.json"] = json.dumps(chain_info, indent=2) + "\n"

        # services/<svc>/tls_config.json — BUGGY service TLS configs
        for svc, cfg in service_configs_buggy.items():
            files[f"services/{svc}/tls_config.json"] = json.dumps(cfg, indent=2) + "\n"

        # renewal_log.json — empty initially; agents must populate with renewal order
        renewal_log_template = {
            "description": "Record each renewal action in order. See spec for required order.",
            "actions": [],
        }
        files["renewal_log.json"] = json.dumps(renewal_log_template, indent=2) + "\n"

        # tests/test_certs.py — validation test suite
        files["tests/test_certs.py"] = _generate_test_py(
            services=services,
            correct_cert_store=correct_cert_store,
            service_configs_correct=service_configs_correct,
            trust_store_path=trust_store_path,
            expired_cert_ids=expired_cert_ids,
        )

        # README.md
        files["README.md"] = _generate_workspace_readme(
            services=services,
            chain_depth=chain_depth,
            root_ca_name=root_ca_name,
            intermediate_cert=intermediate_cert,
            wrong_path_services=wrong_path_services,
            expired_count=len(expired_cert_ids),
        )

        return files


# ---------------------------------------------------------------------------
# Test generator
# ---------------------------------------------------------------------------

def _generate_test_py(
    services: list,
    correct_cert_store: dict,
    service_configs_correct: dict,
    trust_store_path: str,
    expired_cert_ids: list,
) -> str:
    # Use repr() so Python booleans (True/False/None) render correctly in source.
    correct_cert_store_repr = repr(correct_cert_store)
    service_configs_repr = repr(service_configs_correct)
    trust_store_repr = repr(trust_store_path)
    services_repr = repr(services)
    expired_ids_repr = repr(expired_cert_ids)

    return f'''\
"""
tests/test_certs.py — Certificate validation for INC5: Certificate Expiry.

Run with: python3 tests/test_certs.py
       or: python3 -m pytest tests/test_certs.py -v

All tests must pass after certificates and service configs are fixed.
"""
import json
import os
import sys

CORRECT_CERT_STORE = {correct_cert_store_repr}
CORRECT_SERVICE_CONFIGS = {service_configs_repr}
CORRECT_TRUST_STORE = {trust_store_repr}
SERVICES = {services_repr}
ORIGINALLY_EXPIRED_CERT_IDS = {expired_ids_repr}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(rel_path):
    with open(os.path.join(BASE_DIR, rel_path), "r", encoding="utf-8") as f:
        return json.load(f)


def test_cert_store_valid_json():
    """cert_store/certs.json must be valid JSON with at least one entry."""
    store = load_json("cert_store/certs.json")
    assert isinstance(store, dict) and len(store) > 0, "cert_store/certs.json empty or invalid"


def test_cert_store_required_fields():
    """Every cert entry must have cert_path, issuer, status, expires fields."""
    store = load_json("cert_store/certs.json")
    errors = []
    required_fields = {{"cert_path", "issuer", "status", "expires"}}
    for cert_id, entry in store.items():
        missing = required_fields - set(entry.keys())
        if missing:
            errors.append(f"{{cert_id}}: missing fields {{missing}}")
    assert not errors, "Cert store missing required fields:\\n" + "\\n".join(errors)


def test_no_expired_certs_in_store():
    """No cert in cert_store/certs.json should have status=expired after renewal."""
    store = load_json("cert_store/certs.json")
    expired = [cid for cid, entry in store.items() if entry.get("status") == "expired"]
    assert not expired, f"Certs still showing expired status: {{expired}}"


def test_cert_chain_order():
    """Intermediate cert (if present) must have issued_at <= all leaf cert issued_at dates."""
    store = load_json("cert_store/certs.json")
    inter_certs = [e for e in store.values() if e.get("cert_type") == "intermediate_ca"]
    leaf_certs = [e for e in store.values() if e.get("cert_type") == "leaf"]
    errors = []
    for inter in inter_certs:
        inter_issued = inter.get("issued_at", "")
        for leaf in leaf_certs:
            leaf_issued = leaf.get("issued_at", "")
            if inter_issued and leaf_issued and inter_issued > leaf_issued:
                errors.append(
                    f"intermediate {{inter['cert_id']}} issued_at={{inter_issued}} "
                    f"> leaf {{leaf['cert_id']}} issued_at={{leaf_issued}}"
                )
    assert not errors, "Cert chain order violated:\\n" + "\\n".join(errors)


def test_service_configs_valid_json():
    """All service tls_config.json files must be valid JSON."""
    errors = []
    for svc in SERVICES:
        path = os.path.join(BASE_DIR, "services", svc, "tls_config.json")
        if not os.path.exists(path):
            errors.append(f"{{svc}}: tls_config.json missing")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{{svc}}: invalid JSON: {{e}}")
    assert not errors, "Service config errors:\\n" + "\\n".join(errors)


def test_service_configs_reference_valid_certs():
    """Each service's tls_config.json must reference a valid (non-expired) cert path."""
    store = load_json("cert_store/certs.json")
    valid_paths = {{
        entry["cert_path"]
        for entry in store.values()
        if entry.get("status") == "valid"
    }}
    errors = []
    for svc in SERVICES:
        path = os.path.join(BASE_DIR, "services", svc, "tls_config.json")
        if not os.path.exists(path):
            errors.append(f"{{svc}}: tls_config.json missing")
            continue
        cfg = json.load(open(path, "r", encoding="utf-8"))
        tls = cfg.get("tls", {{}})
        cert_path = tls.get("cert_path", "")
        if cert_path not in valid_paths:
            errors.append(f"{{svc}}: cert_path={{cert_path!r}} not in valid certs")
    assert not errors, "Service cert reference errors:\\n" + "\\n".join(errors)


def test_trust_stores_updated():
    """All service configs must use the correct trust store path."""
    errors = []
    for svc in SERVICES:
        path = os.path.join(BASE_DIR, "services", svc, "tls_config.json")
        if not os.path.exists(path):
            errors.append(f"{{svc}}: tls_config.json missing")
            continue
        cfg = json.load(open(path, "r", encoding="utf-8"))
        tls = cfg.get("tls", {{}})
        trust_store = tls.get("trust_store", "")
        if trust_store != CORRECT_TRUST_STORE:
            errors.append(
                f"{{svc}}: trust_store={{trust_store!r}} expected={{CORRECT_TRUST_STORE!r}}"
            )
    assert not errors, "Trust store errors:\\n" + "\\n".join(errors)


def test_no_old_expired_cert_paths_in_configs():
    """No service config should reference old/expired cert paths."""
    store = load_json("cert_store/certs.json")
    # Collect any old_cert_path values recorded in the cert store
    old_paths = {{
        entry["old_cert_path"]
        for entry in store.values()
        if "old_cert_path" in entry
    }}
    errors = []
    for svc in SERVICES:
        path = os.path.join(BASE_DIR, "services", svc, "tls_config.json")
        if not os.path.exists(path):
            continue
        cfg = json.load(open(path, "r", encoding="utf-8"))
        tls = cfg.get("tls", {{}})
        cert_path = tls.get("cert_path", "")
        if cert_path in old_paths:
            errors.append(f"{{svc}}: references old cert path {{cert_path!r}}")
    assert not errors, "Old cert path references:\\n" + "\\n".join(errors)


def test_renewal_log_exists_and_has_actions():
    """renewal_log.json must exist and contain at least one action."""
    path = os.path.join(BASE_DIR, "renewal_log.json")
    assert os.path.exists(path), "renewal_log.json missing"
    log = json.load(open(path, "r", encoding="utf-8"))
    actions = log.get("actions", [])
    assert len(actions) > 0, "renewal_log.json has no actions recorded"


def test_renewal_log_trust_store_first():
    """Trust store update must be the first action in renewal_log.json."""
    path = os.path.join(BASE_DIR, "renewal_log.json")
    if not os.path.exists(path):
        assert False, "renewal_log.json missing"
    log = json.load(open(path, "r", encoding="utf-8"))
    actions = log.get("actions", [])
    if not actions:
        assert False, "renewal_log.json has no actions"
    first_action = actions[0]
    action_type = first_action.get("action", "") if isinstance(first_action, dict) else str(first_action)
    assert "trust_store" in action_type.lower(), (
        f"First renewal action must be trust_store update, got: {{action_type!r}}"
    )


if __name__ == "__main__":
    tests = [
        test_cert_store_valid_json,
        test_cert_store_required_fields,
        test_no_expired_certs_in_store,
        test_cert_chain_order,
        test_service_configs_valid_json,
        test_service_configs_reference_valid_certs,
        test_trust_stores_updated,
        test_no_old_expired_cert_paths_in_configs,
        test_renewal_log_exists_and_has_actions,
        test_renewal_log_trust_store_first,
    ]
    failures = []
    for t in tests:
        try:
            t()
            print(f"PASS  {{t.__name__}}")
        except AssertionError as e:
            print(f"FAIL  {{t.__name__}}: {{e}}")
            failures.append(t.__name__)
        except Exception as e:
            print(f"ERROR {{t.__name__}}: {{e}}")
            failures.append(t.__name__)

    if failures:
        print(f"\\n{{len(failures)}} test(s) failed: {{failures}}")
        sys.exit(1)
    else:
        print(f"\\nAll {{len(tests)}} tests passed.")
        sys.exit(0)
'''


# ---------------------------------------------------------------------------
# Workspace README
# ---------------------------------------------------------------------------

def _generate_workspace_readme(
    services: list,
    chain_depth: int,
    root_ca_name: str,
    intermediate_cert: dict | None,
    wrong_path_services: list,
    expired_count: int,
) -> str:
    chain_desc = f"Root CA ({root_ca_name})"
    if intermediate_cert:
        chain_desc += f" -> Intermediate CA ({intermediate_cert['common_name']})"
    chain_desc += " -> Leaf Certs (one per service)"

    return f"""\
# INC5: Certificate Expiry / TLS Misconfiguration — Workspace

## Services ({len(services)})
{chr(10).join(f"- {svc}" for svc in services)}

## Cert Chain Structure
{chain_desc}

Cert chain depth: {chain_depth}

## Problem Summary

- {expired_count} cert(s) are expired and must be renewed.
- Service configs may reference old/wrong cert paths.
- Trust stores are outdated and must be updated before rotating certs.

## Files to Fix

- `cert_store/certs.json` — Cert metadata store. Expired certs must be renewed
  (status updated to "valid", expires updated). Do NOT change root CA entries.

- `services/<svc>/tls_config.json` — Per-service TLS configuration.
  Must reference valid (non-expired) cert paths. Trust store path must be updated.

- `renewal_log.json` — Record each renewal action in the correct order.
  First action MUST be "update_trust_stores".

## Informational (do not modify)

- `cert_store/chain.json` — Cert chain hierarchy reference.

## Validation

Run the cert tests after fixing:
```bash
python3 tests/test_certs.py
```
Or with pytest:
```bash
python3 -m pytest tests/test_certs.py -v
```

All tests must pass. Do not remove or modify the root CA cert entry.
"""


# ---------------------------------------------------------------------------
# Spec and Brief
# ---------------------------------------------------------------------------

def _generate_spec(
    services: list,
    chain_depth: int,
    root_ca_name: str,
    intermediate_ca_name: str | None,
    intermediate_expired: bool,
    intermediate_cert: dict | None,
    leaf_certs: dict,
    trust_store_path: str,
    renewal_order: list,
    service_configs_correct: dict,
    wrong_path_services: list,
    seed: int,
) -> str:
    # Chain hierarchy diagram
    chain_lines = [f"  {root_ca_name} (root CA, self-signed, always valid)"]
    if intermediate_ca_name and intermediate_cert:
        status_note = " [EXPIRED — must renew first]" if intermediate_expired else ""
        chain_lines.append(f"  └─ {intermediate_ca_name} (intermediate CA){status_note}")
        chain_lines.append(f"     └─ [leaf certs for each service]")
    else:
        chain_lines.append(f"  └─ [leaf certs for each service, issued by root CA]")
    chain_diagram = "\n".join(chain_lines)

    # Service-cert table
    svc_cert_rows = []
    for svc in services:
        lc = leaf_certs[svc]
        status_note = " **[EXPIRED]**" if lc["status"] == "expired" else ""
        svc_cert_rows.append(
            f"| `{svc}` | `{lc['cert_id']}` | `{lc['cert_path']}` | `{lc['issuer']}` |{status_note} |"
        )
    svc_cert_table = "\n".join(svc_cert_rows)

    # Renewal order bullets
    renewal_bullets = []
    for step in renewal_order:
        if step == "update_trust_stores":
            renewal_bullets.append(
                "1. **Update trust stores** on all services to the new CA bundle path "
                f"`{trust_store_path}` — **this must happen BEFORE any cert rotation**."
            )
        elif step.startswith("fix_path:"):
            cert_id = step.split(":", 1)[1]
            renewal_bullets.append(
                f"   - Fix the cert path in tls_config.json for cert `{cert_id}` "
                "(currently points to old/wrong path)."
            )
        elif intermediate_cert and step == intermediate_cert["cert_id"]:
            renewal_bullets.append(
                f"2. **Renew intermediate CA cert** `{step}` — set status=valid, "
                f"update expires. This MUST be done before renewing any leaf certs."
            )
        else:
            renewal_bullets.append(
                f"   - **Renew leaf cert** `{step}` — set status=valid, update expires."
            )
    renewal_section = "\n".join(renewal_bullets)

    # Correct service config table
    svc_cfg_rows = []
    for svc in services:
        cfg = service_configs_correct[svc]
        tls = cfg["tls"]
        svc_cfg_rows.append(
            f"| `{svc}` | `{tls['cert_path']}` | `{tls['trust_store']}` |"
        )
    svc_cfg_table = "\n".join(svc_cfg_rows)

    # Wrong path section
    if wrong_path_services:
        wrong_path_note = (
            "The following services have **wrong cert paths** in their tls_config.json "
            "(they point to old/stale paths that no longer exist):\n"
            + "\n".join(f"- `{svc}`" for svc in wrong_path_services)
        )
    else:
        wrong_path_note = "No services have wrong cert path issues — only expired certs."

    return f"""# INC5: Certificate Expiry / TLS Misconfiguration — Planner Specification

## Incident Summary

**Incident ID**: INC-CERT-{seed:04d}
**Severity**: P1
**Status**: Active — multiple services failing with TLS/SSL errors
**Domain**: Security / Certificate Management

Multiple services have stopped accepting or making TLS connections due to
expired certificates and stale trust stores. This spec provides the complete
cert chain hierarchy, renewal order, and required configuration values needed
to restore service.

---

## Certificate Chain Hierarchy

```
{chain_diagram}
```

**Chain depth**: {chain_depth} levels

**Critical renewal rule**: Intermediate CA certs (if expired) MUST be renewed
before leaf certs. Trust stores MUST be updated before any cert rotation.
Violating this order will cause chain validation failures even after renewal.

---

## Cert Inventory and Status

### Root CA (do not modify)

| Cert ID | Status | Notes |
|---------|--------|-------|
| `{root_ca_name}_cert` | valid | Trusted anchor — never expires within task scope |

{"### Intermediate CA" + chr(10) + chr(10) + f"| Cert ID | Status | Action |" + chr(10) + f"|---------|--------|--------|" + chr(10) + f"| `{intermediate_cert['cert_id']}` | {'**EXPIRED**' if intermediate_expired else 'valid'} | {'Renew intermediate before leaf certs' if intermediate_expired else 'No action needed'} |" + chr(10) if intermediate_cert else ""}
### Leaf Certs (one per service)

| Service | Cert ID | Correct Cert Path | Issuer | Status |
|---------|---------|-------------------|--------|--------|
{svc_cert_table}

---

## Required Renewal Order

The following steps must be performed **in this exact order**:

{renewal_section}

**Constraint**: Do NOT modify the root CA entry (`{root_ca_name}_cert`) in
`cert_store/certs.json`. It is the trusted anchor.

---

## Wrong Cert Path Issues

{wrong_path_note}

---

## Correct Service TLS Configuration

After renewal, each service's `tls_config.json` must have:

| Service | cert_path | trust_store |
|---------|-----------|-------------|
{svc_cfg_table}

**Trust store**: All services must use `{trust_store_path}` as their trust_store value.

---

## Renewal Log Format

Record each action in `renewal_log.json` under the `actions` array:

```json
{{
  "actions": [
    {{"action": "update_trust_stores", "trust_store": "{trust_store_path}", "services": ["all"]}},
    {{"action": "renew_cert", "cert_id": "<cert_id>", "new_expires": "2027-02-26"}},
    ...
  ]
}}
```

The first entry in `actions` MUST have `"action": "update_trust_stores"`.

---

## Fix Procedure

1. **Update `cert_store/certs.json`**:
   - For each expired cert: set `status` to `"valid"`, update `expires` to a future date.
   - Update `issued_at` to today (`2026-02-26`).
   - Do NOT touch the root CA entry.

2. **Fix `services/<svc>/tls_config.json`**:
   - Set `tls.cert_path` to the correct path from the table above.
   - Set `tls.trust_store` to `"{trust_store_path}"` for ALL services.

3. **Update `renewal_log.json`**:
   - Add actions in the required order (trust store update first).

4. **Validate**:
   - Run `python3 tests/test_certs.py` — all tests must pass.
   - Produce `attestation.json` with `verdict="pass"`.

---

## Constraints

- Do NOT modify the root CA cert entry in `cert_store/certs.json`.
- Trust store update MUST precede cert rotation in the renewal log.
- If intermediate CA is expired, renew it BEFORE renewing leaf certs.
- All {len(services)} services must reference valid, non-expired certs.
- `cert_store/chain.json` is informational only — do not modify it.
"""


def _generate_brief(services: list, svc_count: int) -> str:
    return f"""# INC5: Certificate Expiry / TLS Misconfiguration (Brief)

Multiple services are reporting TLS/SSL errors and failing to establish secure
connections. Alerts indicate certificate validation failures across the cluster.

**Services involved** ({svc_count} total):
{chr(10).join(f"- `{svc}`" for svc in services)}

**Workspace structure**:
- `cert_store/certs.json` — Certificate metadata store
- `cert_store/chain.json` — Cert chain hierarchy reference (informational)
- `services/<name>/tls_config.json` — Per-service TLS configuration
- `renewal_log.json` — Log of renewal actions (must be populated in order)
- `tests/test_certs.py` — Certificate validation tests

**Goal**: Diagnose and fix the certificate issues so all services can establish
TLS connections. Ensure cert chain integrity is maintained.

**What to do**:
1. Inspect `cert_store/certs.json` to identify expired certificates.
2. Inspect `services/<svc>/tls_config.json` for incorrect cert paths or stale trust stores.
3. Renew expired certs and update service configs in the correct order.
4. Record each action in `renewal_log.json`.
5. Run `python3 tests/test_certs.py` to verify all cert tests pass.

The Planner has the full cert chain hierarchy, the correct renewal order,
and the exact cert configuration values. Coordinate with the Planner before
making changes — renewal order matters for chain validation.

**Constraint**: Do not modify the root CA cert entry. Do not skip trust store updates.
"""
