#!/usr/bin/env bash
# Seed-aware grader for INC4: DNS / Routing Misconfiguration
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

# ── Check 1: config/services.json valid JSON ──────────────────────────────
check "python3 -c '
import json
with open(\"config/services.json\", \"r\", encoding=\"utf-8\") as f:
    data = json.load(f)
assert isinstance(data, dict) and len(data) > 0
print(\"SERVICES_JSON_VALID\")
'" "services_json_invalid"

# ── Check 2: config/dns.json valid JSON ───────────────────────────────────
check "python3 -c '
import json
with open(\"config/dns.json\", \"r\", encoding=\"utf-8\") as f:
    data = json.load(f)
assert isinstance(data, dict)
print(\"DNS_JSON_VALID\")
'" "dns_json_invalid"

# ── Check 3: config/firewall.json valid JSON ──────────────────────────────
check "python3 -c '
import json
with open(\"config/firewall.json\", \"r\", encoding=\"utf-8\") as f:
    data = json.load(f)
assert isinstance(data, dict) and \"rules\" in data
print(\"FIREWALL_JSON_VALID\")
'" "firewall_json_invalid"

# ── Check 4: All DNS entries present with correct hostnames ───────────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
correct_dns = expected[\"correct_dns\"]
dns = json.load(open(\"config/dns.json\", encoding=\"utf-8\"))
errors = []
for svc, exp in correct_dns.items():
    if svc not in dns:
        errors.append(f\"Missing DNS entry for {svc}\")
        continue
    actual = dns[svc].get(\"hostname\")
    exp_host = exp[\"hostname\"]
    if actual != exp_host:
        errors.append(f\"{svc}: hostname={actual!r} expected={exp_host!r}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"DNS_HOSTNAMES_OK\")
'" "dns_hostnames_wrong"

# ── Check 5: All DNS port values correct ──────────────────────────────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
correct_ports = expected[\"correct_ports\"]
dns = json.load(open(\"config/dns.json\", encoding=\"utf-8\"))
errors = []
for svc, exp_port in correct_ports.items():
    if svc not in dns:
        errors.append(f\"Missing DNS entry for {svc}\")
        continue
    actual_port = dns[svc].get(\"port\")
    if actual_port != exp_port:
        errors.append(f\"{svc}: port={actual_port} expected={exp_port}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"DNS_PORTS_OK\")
'" "dns_ports_wrong"

# ── Check 6: All DNS protocol values correct ──────────────────────────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
correct_protocols = expected[\"correct_protocols\"]
dns = json.load(open(\"config/dns.json\", encoding=\"utf-8\"))
errors = []
for svc, exp_proto in correct_protocols.items():
    if svc not in dns:
        errors.append(f\"Missing DNS entry for {svc}\")
        continue
    actual_proto = dns[svc].get(\"protocol\")
    if actual_proto != exp_proto:
        errors.append(f\"{svc}: protocol={actual_proto!r} expected={exp_proto!r}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"DNS_PROTOCOLS_OK\")
'" "dns_protocols_wrong"

# ── Check 7: Firewall allows all required service-to-service edges ─────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
required_edges = [(e[0], e[1]) for e in expected[\"correct_firewall_edges\"]]
fw = json.load(open(\"config/firewall.json\", encoding=\"utf-8\"))
rules = fw.get(\"rules\", [])
allowed = {(r[\"source\"], r[\"destination\"]) for r in rules if r.get(\"action\") == \"allow\"}
blocked = [(s, d) for s, d in required_edges if (s, d) not in allowed]
if blocked:
    print(f\"Firewall blocks required edges: {blocked}\")
    sys.exit(1)
print(\"FIREWALL_EDGES_OK\")
'" "firewall_missing_rules"

# ── Check 8: No overly permissive wildcard rules ──────────────────────────
check "python3 -c '
import json, sys
fw = json.load(open(\"config/firewall.json\", encoding=\"utf-8\"))
rules = fw.get(\"rules\", [])
bad = []
for r in rules:
    src = r.get(\"source\", \"\")
    dst = r.get(\"destination\", \"\")
    if src in (\"*\", \"all\", \"any\", \"\") or dst in (\"*\", \"all\", \"any\", \"\"):
        bad.append(r)
if bad:
    print(f\"Wildcard/permissive rules found: {bad}\")
    sys.exit(1)
print(\"NO_WILDCARD_RULES\")
'" "firewall_overly_permissive"

# ── Check 9: Service connection configs reference correct DNS names ─────────
check "python3 -c '
import json, sys, os
expected = json.load(open(\"$EXPECTED\"))
correct_dns = expected[\"correct_dns\"]
correct_ports = expected[\"correct_ports\"]
required_edges = [(e[0], e[1]) for e in expected[\"correct_firewall_edges\"]]
errors = []
for src, dst in required_edges:
    conn_path = os.path.join(\"services\", src, \"connection.json\")
    if not os.path.exists(conn_path):
        errors.append(f\"{src}: connection.json missing\")
        continue
    conn = json.load(open(conn_path, encoding=\"utf-8\"))
    upstreams = conn.get(\"upstreams\", {})
    if dst not in upstreams:
        continue  # upstream section optional for some topologies
    upstream = upstreams[dst]
    actual_dns = upstream.get(\"dns_name\")
    exp_hostname = correct_dns.get(dst, {}).get(\"hostname\")
    if actual_dns != exp_hostname:
        errors.append(f\"{src}->{dst}: dns_name={actual_dns!r} expected={exp_hostname!r}\")
    actual_port = upstream.get(\"port\")
    exp_port = correct_ports.get(dst)
    if actual_port != exp_port:
        errors.append(f\"{src}->{dst}: port={actual_port} expected={exp_port}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"SERVICE_CONFIGS_OK\")
'" "service_configs_wrong"

# ── Check 10: tests/test_connectivity.py runs and passes ──────────────────
check "python3 tests/test_connectivity.py" "connectivity_tests_fail"

# ── Check 11: No required edge blocked by firewall (double-check with ports) ─
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
correct_ports = expected[\"correct_ports\"]
required_edges = [(e[0], e[1]) for e in expected[\"correct_firewall_edges\"]]
fw = json.load(open(\"config/firewall.json\", encoding=\"utf-8\"))
rules = fw.get(\"rules\", [])
errors = []
for src, dst in required_edges:
    exp_port = correct_ports.get(dst)
    matching = [
        r for r in rules
        if r.get(\"source\") == src
        and r.get(\"destination\") == dst
        and r.get(\"action\") == \"allow\"
    ]
    if not matching:
        errors.append(f\"No allow rule for {src}->{dst}\")
        continue
    # Check at least one rule has correct port
    port_ok = any(r.get(\"port\") == exp_port for r in matching)
    if not port_ok:
        actual_ports = [r.get(\"port\") for r in matching]
        errors.append(f\"{src}->{dst}: rule port(s)={actual_ports} expected={exp_port}\")
if errors:
    print(\"ERRORS:\", errors)
    sys.exit(1)
print(\"FIREWALL_PORTS_OK\")
'" "firewall_ports_wrong"

# ── Check 12: Attestation verdict=pass ───────────────────────────────────
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
