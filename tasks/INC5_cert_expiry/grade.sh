#!/usr/bin/env bash
# Seed-aware grader for INC5: Certificate Expiry / TLS Misconfiguration
# Reads expected values from expected.json for seed-specific grading.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

cd "$WORKSPACE"

# ── Check 1: cert_store/certs.json valid JSON ─────────────────────────────
check "python3 -c '
import json
with open(\"cert_store/certs.json\", \"r\", encoding=\"utf-8\") as f:
    data = json.load(f)
assert isinstance(data, dict) and len(data) > 0
print(\"CERT_STORE_JSON_VALID\")
'" "cert_store_json_invalid"

# ── Check 2: All cert entries have required fields ─────────────────────────
check "python3 -c '
import json, sys
store = json.load(open(\"cert_store/certs.json\", encoding=\"utf-8\"))
required = {\"cert_path\", \"issuer\", \"status\", \"expires\"}
errors = []
for cid, entry in store.items():
    missing = required - set(entry.keys())
    if missing:
        errors.append(f\"{cid}: missing {missing}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"CERT_FIELDS_OK\")
'" "cert_store_missing_fields"

# ── Check 3: No cert has status=expired ───────────────────────────────────
check "python3 -c '
import json, sys
store = json.load(open(\"cert_store/certs.json\", encoding=\"utf-8\"))
expired = [cid for cid, e in store.items() if e.get(\"status\") == \"expired\"]
if expired:
    print(f\"Still expired: {expired}\")
    sys.exit(1)
print(\"NO_EXPIRED_CERTS\")
'" "certs_still_expired"

# ── Check 4: Cert chain order correct (intermediate issued_at <= leaf) ─────
check "python3 -c '
import json, sys
store = json.load(open(\"cert_store/certs.json\", encoding=\"utf-8\"))
inter_certs = [e for e in store.values() if e.get(\"cert_type\") == \"intermediate_ca\"]
leaf_certs = [e for e in store.values() if e.get(\"cert_type\") == \"leaf\"]
errors = []
for inter in inter_certs:
    inter_issued = inter.get(\"issued_at\", \"\")
    for leaf in leaf_certs:
        leaf_issued = leaf.get(\"issued_at\", \"\")
        if inter_issued and leaf_issued and inter_issued > leaf_issued:
            errors.append(
                f\"intermediate {inter[chr(39)+\"cert_id\"+chr(39)]} issued_at={inter_issued} \"
                f\"> leaf {leaf[chr(39)+\"cert_id\"+chr(39)]} issued_at={leaf_issued}\"
            )
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"CHAIN_ORDER_OK\")
'" "chain_order_violated"

# ── Check 5: All services reference valid cert paths ──────────────────────
check "python3 -c '
import json, sys, os
expected = json.load(open(\"$EXPECTED\"))
services = expected[\"services\"]
store = json.load(open(\"cert_store/certs.json\", encoding=\"utf-8\"))
valid_paths = {e[\"cert_path\"] for e in store.values() if e.get(\"status\") == \"valid\"}
errors = []
for svc in services:
    path = os.path.join(\"services\", svc, \"tls_config.json\")
    if not os.path.exists(path):
        errors.append(f\"{svc}: tls_config.json missing\")
        continue
    cfg = json.load(open(path, encoding=\"utf-8\"))
    cert_path = cfg.get(\"tls\", {}).get(\"cert_path\", \"\")
    if cert_path not in valid_paths:
        errors.append(f\"{svc}: cert_path={cert_path!r} not in valid certs\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"SERVICE_CERT_REFS_OK\")
'" "service_cert_refs_invalid"

# ── Check 6: Service tls_config.json files are valid JSON ─────────────────
check "python3 -c '
import json, sys, os
expected = json.load(open(\"$EXPECTED\"))
services = expected[\"services\"]
errors = []
for svc in services:
    path = os.path.join(\"services\", svc, \"tls_config.json\")
    if not os.path.exists(path):
        errors.append(f\"{svc}: tls_config.json missing\")
        continue
    try:
        json.load(open(path, encoding=\"utf-8\"))
    except Exception as e:
        errors.append(f\"{svc}: invalid JSON: {e}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"SERVICE_CONFIGS_VALID_JSON\")
'" "service_configs_invalid_json"

# ── Check 7: Trust stores updated for all services ────────────────────────
check "python3 -c '
import json, sys, os
expected = json.load(open(\"$EXPECTED\"))
services = expected[\"services\"]
correct_trust_store = expected[\"trust_store_path\"]
errors = []
for svc in services:
    path = os.path.join(\"services\", svc, \"tls_config.json\")
    if not os.path.exists(path):
        errors.append(f\"{svc}: tls_config.json missing\")
        continue
    cfg = json.load(open(path, encoding=\"utf-8\"))
    trust_store = cfg.get(\"tls\", {}).get(\"trust_store\", \"\")
    if trust_store != correct_trust_store:
        errors.append(f\"{svc}: trust_store={trust_store!r} expected={correct_trust_store!r}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"TRUST_STORES_OK\")
'" "trust_stores_stale"

# ── Check 8: renewal_log.json exists with correct order (trust store first) ─
check "python3 -c '
import json, sys, os
log_path = \"renewal_log.json\"
if not os.path.exists(log_path):
    print(\"renewal_log.json missing\")
    sys.exit(1)
log = json.load(open(log_path, encoding=\"utf-8\"))
actions = log.get(\"actions\", [])
if not actions:
    print(\"renewal_log.json has no actions\")
    sys.exit(1)
first = actions[0]
action_type = first.get(\"action\", \"\") if isinstance(first, dict) else str(first)
if \"trust_store\" not in action_type.lower():
    print(f\"First action must be trust_store update, got: {action_type!r}\")
    sys.exit(1)
print(\"RENEWAL_LOG_OK\")
'" "renewal_log_wrong_order"

# ── Check 9: No service config references old expired cert paths ───────────
check "python3 -c '
import json, sys, os
expected = json.load(open(\"$EXPECTED\"))
services = expected[\"services\"]
store = json.load(open(\"cert_store/certs.json\", encoding=\"utf-8\"))
old_paths = {e[\"old_cert_path\"] for e in store.values() if \"old_cert_path\" in e}
errors = []
for svc in services:
    path = os.path.join(\"services\", svc, \"tls_config.json\")
    if not os.path.exists(path):
        continue
    cfg = json.load(open(path, encoding=\"utf-8\"))
    cert_path = cfg.get(\"tls\", {}).get(\"cert_path\", \"\")
    if cert_path in old_paths:
        errors.append(f\"{svc}: still references old cert path {cert_path!r}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"NO_OLD_PATHS\")
'" "old_cert_paths_still_referenced"

# ── Check 10: tests/test_certs.py runs and passes ─────────────────────────
check "python3 tests/test_certs.py" "cert_tests_fail"

# ── Check 11: Attestation verdict=pass ───────────────────────────────────
check "python3 -c '
import json, sys
att = json.load(open(\"$SUBMISSION/attestation.json\"))
assert att.get(\"verdict\") == \"pass\", f\"verdict={att.get(chr(39)+chr(118)+chr(101)+chr(114)+chr(100)+chr(105)+chr(99)+chr(116)+chr(39))!r}\"
print(\"ATTESTATION_OK\")
'" "bad_attestation"

# ── Write score ───────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
