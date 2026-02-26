"""
Parameterized generator for INC4: DNS / Routing Misconfiguration.

Each seed produces:
  - Different service count (3-5 services)
  - Different topology (star, mesh, chain)
  - Different bug types per edge:
      * wrong_hostname  — DNS entry points to wrong host
      * wrong_port      — port number is off
      * missing_dns     — DNS entry absent entirely
      * firewall_block  — firewall rule missing (traffic not allowed)
      * wrong_protocol  — http vs https mismatch
  - Different service names drawn from realistic microservice pools

TNI driver: The spec (Planner) has the full correct network topology — which
services must reach which, the correct DNS hostname, correct port, correct
protocol, and correct firewall allowlist. The brief (Executor) only says
"several microservices are failing to communicate; diagnose and fix the
networking configuration." Without the Planner's topology the Executor cannot
know what the CORRECT configuration should be for each service pair.

The grader checks (12 checks):
  1.  config/services.json valid JSON
  2.  config/dns.json valid JSON
  3.  config/firewall.json valid JSON
  4.  All DNS entries present and hostname correct
  5.  All DNS port values correct
  6.  All DNS protocol values correct
  7.  Firewall allows all required service-to-service edges
  8.  No overly-permissive wildcard rules (must not allow "all"/"*" sources)
  9.  services/ connection configs reference correct DNS names
  10. tests/test_connectivity.py runs and passes
  11. No required edge is blocked by firewall
  12. Attestation verdict=pass
"""
from __future__ import annotations

import json

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ---------------------------------------------------------------------------
# Service name pools
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
    "recommendation_service",
    "audit_service",
    "reporting_service",
    "cache_service",
    "queue_service",
    "metrics_service",
]

# Hostname suffix options — used in DNS entries
_HOST_SUFFIXES = [
    ".internal",
    ".svc.local",
    ".cluster.local",
    ".private",
    ".corp",
]

# Protocol pairs: (correct_protocol, wrong_protocol)
_PROTOCOL_PAIRS = [
    ("http", "https"),
    ("https", "http"),
    ("http", "grpc"),
    ("https", "grpc"),
]

# Bug types
_BUG_TYPES = [
    "wrong_hostname",
    "wrong_port",
    "missing_dns",
    "firewall_block",
    "wrong_protocol",
]

# Topology types
_TOPOLOGIES = ["star", "mesh", "chain"]

# Port pool — realistic microservice ports
_PORT_POOL = [8080, 8081, 8443, 9000, 9001, 9090, 3000, 3001, 4000, 4001,
              5000, 5001, 6000, 6001, 7000, 7001, 8000, 8001, 8100, 8200]


class Generator(TaskGenerator):
    task_id = "INC4_dns_miscfg"
    domain = "incident_response"
    difficulty = "hard"
    languages = ["python", "json", "bash"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # --- Choose variant parameters ---
        svc_count = 3 + (seed % 3)   # 3, 4, or 5
        topology = _TOPOLOGIES[seed % len(_TOPOLOGIES)]
        host_suffix = _HOST_SUFFIXES[(seed * 3 + 1) % len(_HOST_SUFFIXES)]

        # Pick services
        all_svcs = list(_SVC_POOL)
        rng.shuffle(all_svcs)
        services = all_svcs[:svc_count]

        # Assign correct ports (unique)
        port_pool = list(_PORT_POOL)
        rng.shuffle(port_pool)
        correct_ports = {svc: port_pool[i] for i, svc in enumerate(services)}

        # Correct hostnames: svc-name + suffix (dashes for underscores)
        def canonical_host(svc: str) -> str:
            return svc.replace("_", "-") + host_suffix

        correct_hosts = {svc: canonical_host(svc) for svc in services}

        # Correct protocols
        proto_pair = _PROTOCOL_PAIRS[(seed * 7 + 2) % len(_PROTOCOL_PAIRS)]
        correct_protocol = proto_pair[0]
        wrong_protocol = proto_pair[1]
        # All services use the same protocol for simplicity
        correct_protocols = {svc: correct_protocol for svc in services}

        # --- Build edges (service communication requirements) ---
        edges = _build_edges(services, topology, rng)

        # --- Decide which edges get which bugs ---
        # Each edge independently can have a bug; we ensure at least 2 bugs,
        # at most min(len(edges), 4) bugs.
        num_bugs = min(len(edges), max(2, 2 + (seed % 3)))
        bug_edge_indices = list(range(len(edges)))
        rng.shuffle(bug_edge_indices)
        bug_edge_indices = bug_edge_indices[:num_bugs]

        bug_pool = list(_BUG_TYPES)
        rng.shuffle(bug_pool)

        edge_bugs: dict[tuple, str] = {}
        for i, ei in enumerate(bug_edge_indices):
            edge_bugs[edges[ei]] = bug_pool[i % len(bug_pool)]

        # --- Build correct DNS table ---
        correct_dns: dict[str, dict] = {}
        for svc in services:
            correct_dns[svc] = {
                "hostname": correct_hosts[svc],
                "port": correct_ports[svc],
                "protocol": correct_protocols[svc],
            }

        # --- Build buggy DNS table (start from correct, apply bugs) ---
        buggy_dns: dict[str, dict] = {
            svc: dict(entry) for svc, entry in correct_dns.items()
        }

        # Track which bugs affect DNS vs firewall vs service config
        dns_bugs: dict[str, str] = {}      # svc -> bug_type
        firewall_bugs: list[tuple] = []    # (src, dst) edges blocked
        service_cfg_bugs: dict[tuple, str] = {}  # (src, dst) -> bug_type

        for (src, dst), bug in edge_bugs.items():
            if bug == "wrong_hostname":
                # Corrupt the destination hostname in DNS
                bad_host = "wrong-host" + host_suffix
                buggy_dns[dst]["hostname"] = bad_host
                dns_bugs[dst] = "wrong_hostname"
            elif bug == "wrong_port":
                # Off-by-one port in DNS
                buggy_dns[dst]["port"] = correct_ports[dst] + 1
                dns_bugs[dst] = "wrong_port"
            elif bug == "missing_dns":
                # Remove the DNS entry for dst entirely
                if dst in buggy_dns:
                    del buggy_dns[dst]
                dns_bugs[dst] = "missing_dns"
            elif bug == "firewall_block":
                # Mark this edge as having a missing firewall rule
                firewall_bugs.append((src, dst))
            elif bug == "wrong_protocol":
                # Wrong protocol in DNS
                buggy_dns[dst]["protocol"] = wrong_protocol
                dns_bugs[dst] = "wrong_protocol"

        # --- Build firewall rules ---
        # Correct firewall: all edges allowed, from specific source to specific dst
        correct_firewall_rules = [
            {
                "source": src,
                "destination": dst,
                "port": correct_ports[dst],
                "action": "allow",
            }
            for src, dst in edges
        ]

        # Buggy firewall: omit rules for firewall_blocked edges
        buggy_firewall_rules = [
            rule for rule in correct_firewall_rules
            if (rule["source"], rule["destination"]) not in firewall_bugs
        ]

        # --- Build service connection configs (services/ directory) ---
        service_configs: dict[str, dict] = {}
        for svc in services:
            # Each service has a connection config listing its upstream dependencies
            upstreams = {}
            for (src, dst) in edges:
                if src == svc:
                    # Pull connection info from the (buggy) DNS table
                    dns_entry = buggy_dns.get(dst, {})
                    upstreams[dst] = {
                        "dns_name": dns_entry.get("hostname", "MISSING"),
                        "port": dns_entry.get("port", 0),
                        "protocol": dns_entry.get("protocol", "http"),
                    }
            service_configs[svc] = {
                "service_name": svc,
                "host": correct_hosts[svc],
                "port": correct_ports[svc],
                "upstreams": upstreams,
            }

        # --- Build expected dict (grader ground truth) ---
        expected = {
            "services": services,
            "topology": topology,
            "host_suffix": host_suffix,
            "correct_protocol": correct_protocol,
            "edges": [list(e) for e in edges],
            "correct_dns": correct_dns,
            "correct_ports": correct_ports,
            "correct_hosts": correct_hosts,
            "correct_protocols": correct_protocols,
            "correct_firewall_edges": [[src, dst] for src, dst in edges],
            "buggy_edges": {
                f"{src}->{dst}": bug
                for (src, dst), bug in edge_bugs.items()
            },
            "firewall_blocked_edges": [[src, dst] for src, dst in firewall_bugs],
            "dns_buggy_services": dns_bugs,
        }

        # --- Build workspace files ---
        workspace_files = self._build_workspace(
            services=services,
            topology=topology,
            edges=edges,
            correct_dns=correct_dns,
            buggy_dns=buggy_dns,
            correct_ports=correct_ports,
            correct_hosts=correct_hosts,
            correct_protocols=correct_protocols,
            correct_firewall_rules=correct_firewall_rules,
            buggy_firewall_rules=buggy_firewall_rules,
            service_configs=service_configs,
            edge_bugs=edge_bugs,
            correct_protocol=correct_protocol,
        )

        spec_md = _generate_spec(
            services=services,
            topology=topology,
            edges=edges,
            correct_dns=correct_dns,
            correct_ports=correct_ports,
            correct_hosts=correct_hosts,
            correct_protocols=correct_protocols,
            correct_firewall_rules=correct_firewall_rules,
            edge_bugs=edge_bugs,
            firewall_bugs=firewall_bugs,
            host_suffix=host_suffix,
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
        topology: str,
        edges: list,
        correct_dns: dict,
        buggy_dns: dict,
        correct_ports: dict,
        correct_hosts: dict,
        correct_protocols: dict,
        correct_firewall_rules: list,
        buggy_firewall_rules: list,
        service_configs: dict,
        edge_bugs: dict,
        correct_protocol: str,
    ) -> dict[str, str]:
        files: dict[str, str] = {}

        # config/services.json — service registry (correct host/port per service)
        svc_registry = {
            svc: {
                "service_name": svc,
                "host": correct_hosts[svc],
                "port": correct_ports[svc],
                "protocol": correct_protocols[svc],
                "health_path": "/health",
            }
            for svc in services
        }
        files["config/services.json"] = json.dumps(svc_registry, indent=2) + "\n"

        # config/dns.json — DNS table (BUGGY — agents must fix)
        files["config/dns.json"] = json.dumps(buggy_dns, indent=2) + "\n"

        # config/firewall.json — firewall rules (BUGGY — missing some edges)
        firewall_obj = {"rules": buggy_firewall_rules, "default_action": "deny"}
        files["config/firewall.json"] = json.dumps(firewall_obj, indent=2) + "\n"

        # services/<svc>/connection.json — per-service upstream connection config
        for svc, cfg in service_configs.items():
            files[f"services/{svc}/connection.json"] = json.dumps(cfg, indent=2) + "\n"

        # tests/test_connectivity.py — connectivity validation tests
        files["tests/test_connectivity.py"] = _generate_test_py(
            services=services,
            edges=edges,
            correct_dns=correct_dns,
            correct_ports=correct_ports,
            correct_protocols=correct_protocols,
        )

        # README.md for workspace orientation
        files["README.md"] = _generate_workspace_readme(
            services=services, topology=topology, edges=edges
        )

        return files


# ---------------------------------------------------------------------------
# Topology helpers
# ---------------------------------------------------------------------------

def _build_edges(services: list, topology: str, rng: SeededRandom) -> list[tuple]:
    """Return a list of directed (src, dst) communication edges."""
    if topology == "star":
        # services[0] is the hub; it talks to all others
        hub = services[0]
        return [(hub, svc) for svc in services[1:]]
    elif topology == "mesh":
        # Every service talks to every other (up to 4 services to keep manageable)
        edges = []
        for i, src in enumerate(services):
            for j, dst in enumerate(services):
                if i != j:
                    edges.append((src, dst))
        # For large mesh, cap at reasonable number
        if len(edges) > 8:
            rng.shuffle(edges)
            edges = edges[:8]
        return edges
    else:  # chain: A -> B -> C -> ...
        return [(services[i], services[i + 1]) for i in range(len(services) - 1)]


# ---------------------------------------------------------------------------
# Test generator
# ---------------------------------------------------------------------------

def _generate_test_py(
    services: list,
    edges: list,
    correct_dns: dict,
    correct_ports: dict,
    correct_protocols: dict,
) -> str:
    edges_repr = json.dumps([[s, d] for s, d in edges])
    correct_dns_repr = json.dumps(correct_dns, indent=4)
    correct_ports_repr = json.dumps(correct_ports, indent=4)
    correct_protocols_repr = json.dumps(correct_protocols, indent=4)
    services_repr = json.dumps(services)

    return f'''\
"""
tests/test_connectivity.py — Connectivity validation for INC4: DNS Misconfiguration.

These tests validate that the network configuration files are correct.
Run with: python3 -m pytest tests/test_connectivity.py -v
       or: python3 tests/test_connectivity.py

All tests must pass after the DNS and firewall configuration is fixed.
"""
import json
import os
import sys

# Correct expected values (provided by grader / spec)
EXPECTED_DNS = {correct_dns_repr}
EXPECTED_PORTS = {correct_ports_repr}
EXPECTED_PROTOCOLS = {correct_protocols_repr}
REQUIRED_EDGES = {edges_repr}
SERVICES = {services_repr}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(rel_path):
    with open(os.path.join(BASE_DIR, rel_path), "r", encoding="utf-8") as f:
        return json.load(f)


def test_dns_all_entries_present():
    """Every service must have a DNS entry."""
    dns = load_json("config/dns.json")
    missing = [svc for svc in SERVICES if svc not in dns]
    assert not missing, f"Missing DNS entries for: {{missing}}"


def test_dns_hostnames_correct():
    """All DNS hostnames must match expected values."""
    dns = load_json("config/dns.json")
    errors = []
    for svc, expected in EXPECTED_DNS.items():
        if svc not in dns:
            errors.append(f"{{svc}}: DNS entry missing")
            continue
        actual_host = dns[svc].get("hostname")
        exp_host = expected["hostname"]
        if actual_host != exp_host:
            errors.append(f"{{svc}}: hostname={{actual_host!r}} expected={{exp_host!r}}")
    assert not errors, "DNS hostname errors:\\n" + "\\n".join(errors)


def test_dns_ports_correct():
    """All DNS port values must match expected values."""
    dns = load_json("config/dns.json")
    errors = []
    for svc, expected_port in EXPECTED_PORTS.items():
        if svc not in dns:
            errors.append(f"{{svc}}: DNS entry missing, cannot check port")
            continue
        actual_port = dns[svc].get("port")
        if actual_port != expected_port:
            errors.append(f"{{svc}}: port={{actual_port}} expected={{expected_port}}")
    assert not errors, "DNS port errors:\\n" + "\\n".join(errors)


def test_dns_protocols_correct():
    """All DNS protocol values must match expected values."""
    dns = load_json("config/dns.json")
    errors = []
    for svc, expected_proto in EXPECTED_PROTOCOLS.items():
        if svc not in dns:
            errors.append(f"{{svc}}: DNS entry missing, cannot check protocol")
            continue
        actual_proto = dns[svc].get("protocol")
        if actual_proto != expected_proto:
            errors.append(f"{{svc}}: protocol={{actual_proto!r}} expected={{expected_proto!r}}")
    assert not errors, "DNS protocol errors:\\n" + "\\n".join(errors)


def test_firewall_allows_required_edges():
    """Firewall must allow all required service-to-service edges."""
    fw = load_json("config/firewall.json")
    rules = fw.get("rules", [])
    allowed_pairs = {{(r["source"], r["destination"]) for r in rules if r.get("action") == "allow"}}
    blocked = []
    for src, dst in REQUIRED_EDGES:
        if (src, dst) not in allowed_pairs:
            blocked.append(f"{{src}} -> {{dst}}")
    assert not blocked, f"Firewall blocks required edges: {{blocked}}"


def test_firewall_not_overly_permissive():
    """Firewall must not contain wildcard/all-source rules."""
    fw = load_json("config/firewall.json")
    rules = fw.get("rules", [])
    bad_rules = []
    for rule in rules:
        src = rule.get("source", "")
        dst = rule.get("destination", "")
        if src in ("*", "all", "any", "") or dst in ("*", "all", "any", ""):
            bad_rules.append(rule)
    assert not bad_rules, f"Overly permissive firewall rules found: {{bad_rules}}"


def test_firewall_correct_ports():
    """Firewall allow rules must reference correct destination ports."""
    fw = load_json("config/firewall.json")
    rules = fw.get("rules", [])
    errors = []
    for rule in rules:
        if rule.get("action") != "allow":
            continue
        dst = rule.get("destination")
        fw_port = rule.get("port")
        exp_port = EXPECTED_PORTS.get(dst)
        if exp_port is not None and fw_port != exp_port:
            errors.append(f"Rule {{rule.get('source')}}->{{dst}}: port={{fw_port}} expected={{exp_port}}")
    assert not errors, "Firewall port errors:\\n" + "\\n".join(errors)


def test_service_connection_configs():
    """Each service connection config must reference correct DNS name and port."""
    errors = []
    for svc in SERVICES:
        conn_path = os.path.join(BASE_DIR, "services", svc, "connection.json")
        if not os.path.exists(conn_path):
            errors.append(f"{{svc}}: connection.json missing")
            continue
        with open(conn_path, "r", encoding="utf-8") as f:
            conn = json.load(f)
        upstreams = conn.get("upstreams", {{}})
        for src, dst in REQUIRED_EDGES:
            if src != svc:
                continue
            if dst not in upstreams:
                continue  # upstream might be empty if no upstreams for this svc
            upstream_cfg = upstreams[dst]
            exp_dns = EXPECTED_DNS.get(dst, {{}})
            actual_dns_name = upstream_cfg.get("dns_name")
            exp_hostname = exp_dns.get("hostname")
            if actual_dns_name != exp_hostname:
                errors.append(
                    f"{{svc}} -> {{dst}}: dns_name={{actual_dns_name!r}} expected={{exp_hostname!r}}"
                )
            actual_port = upstream_cfg.get("port")
            exp_port = EXPECTED_PORTS.get(dst)
            if actual_port != exp_port:
                errors.append(
                    f"{{svc}} -> {{dst}}: port={{actual_port}} expected={{exp_port}}"
                )
    assert not errors, "Service config errors:\\n" + "\\n".join(errors)


if __name__ == "__main__":
    tests = [
        test_dns_all_entries_present,
        test_dns_hostnames_correct,
        test_dns_ports_correct,
        test_dns_protocols_correct,
        test_firewall_allows_required_edges,
        test_firewall_not_overly_permissive,
        test_firewall_correct_ports,
        test_service_connection_configs,
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
# README for workspace
# ---------------------------------------------------------------------------

def _generate_workspace_readme(services: list, topology: str, edges: list) -> str:
    edge_lines = "\n".join(f"  {src} -> {dst}" for src, dst in edges)
    return f"""\
# INC4: DNS / Routing Misconfiguration — Workspace

## Services ({len(services)})
{chr(10).join(f"- {svc}" for svc in services)}

## Topology: {topology}

### Required Communication Edges
{edge_lines}

## Files to Fix

- `config/dns.json` — DNS table mapping service names to hostname/port/protocol.
  Some entries have wrong hostnames, wrong ports, wrong protocols, or are missing.

- `config/firewall.json` — Firewall allow-list for service-to-service traffic.
  Some required edges may be missing from the rules.

- `services/<svc>/connection.json` — Per-service upstream connection config.
  Must reference correct DNS names and ports.

## Validation

Run the connectivity tests after fixing:
```bash
python3 tests/test_connectivity.py
```
Or with pytest:
```bash
python3 -m pytest tests/test_connectivity.py -v
```

All tests must pass. Do not add wildcard/permissive firewall rules.
"""


# ---------------------------------------------------------------------------
# Spec and Brief
# ---------------------------------------------------------------------------

def _generate_spec(
    services: list,
    topology: str,
    edges: list,
    correct_dns: dict,
    correct_ports: dict,
    correct_hosts: dict,
    correct_protocols: dict,
    correct_firewall_rules: list,
    edge_bugs: dict,
    firewall_bugs: list,
    host_suffix: str,
    seed: int,
) -> str:
    # Topology diagram
    if topology == "star":
        hub = services[0]
        topo_lines = "\n".join(f"  {hub} --> {svc}" for svc in services[1:])
        topo_diagram = f"Star topology (hub: {hub})\n{topo_lines}"
    elif topology == "mesh":
        topo_lines = "\n".join(f"  {src} --> {dst}" for src, dst in edges)
        topo_diagram = f"Mesh topology\n{topo_lines}"
    else:
        topo_lines = " -> ".join(services)
        topo_diagram = f"Chain topology\n  {topo_lines}"

    # DNS table (correct)
    dns_table_rows = []
    for svc in services:
        entry = correct_dns[svc]
        dns_table_rows.append(
            f"| `{svc}` | `{entry['hostname']}` | `{entry['port']}` | `{entry['protocol']}` |"
        )
    dns_table = "\n".join(dns_table_rows)

    # Firewall table (correct)
    fw_table_rows = [
        f"| `{r['source']}` | `{r['destination']}` | `{r['port']}` | allow |"
        for r in correct_firewall_rules
    ]
    fw_table = "\n".join(fw_table_rows)

    # Bug summary for Planner
    bug_lines = []
    for (src, dst), bug in edge_bugs.items():
        bug_lines.append(f"- Edge `{src} -> {dst}`: **{bug}**")
    bug_summary = "\n".join(bug_lines) if bug_lines else "- (none)"

    # Firewall bug summary
    fw_bug_lines = [
        f"- Missing rule: `{src}` -> `{dst}` (port {correct_ports[dst]})"
        for src, dst in firewall_bugs
    ]
    fw_bug_summary = "\n".join(fw_bug_lines) if fw_bug_lines else "- (none)"

    return f"""# INC4: DNS / Routing Misconfiguration — Planner Specification

## Incident Summary

**Incident ID**: INC-NET-{seed:04d}
**Severity**: P1
**Status**: Active — multiple service-to-service communication failures
**Domain**: Networking / DNS / Firewall

Several microservices in the cluster are unable to communicate. The root cause
is a combination of DNS misconfiguration, incorrect port mappings, and missing
firewall rules introduced during a recent infrastructure rotation.

---

## Network Topology

```
{topo_diagram}
```

The following service-to-service communication paths are **required** and must
all be functional after the fix:

| Source | Destination |
|--------|-------------|
{chr(10).join(f"| `{src}` | `{dst}` |" for src, dst in edges)}

---

## Correct DNS Configuration

The `config/dns.json` file must map every service to its correct DNS entry.
The table below shows the **correct** values that must be restored:

| Service | Hostname | Port | Protocol |
|---------|----------|------|----------|
{dns_table}

**Hostname convention**: all internal hostnames use the `{host_suffix}` suffix,
derived from the service name with underscores replaced by hyphens.
Example: `user_service` → `user-service{host_suffix}`

---

## Correct Firewall Rules

The `config/firewall.json` must contain an explicit **allow** rule for every
required service-to-service edge. The default action is `deny`.

| Source | Destination | Port | Action |
|--------|-------------|------|--------|
{fw_table}

**Constraint**: Do NOT add wildcard rules (`source: "*"` or `destination: "*"`).
Every rule must specify an explicit source and destination service name.

---

## Known Bugs Introduced (Root Cause)

### DNS Bugs
{bug_summary if any(v != "firewall_block" for v in edge_bugs.values()) else "- (all bugs are firewall-type)"}

### Firewall Bugs (missing allow rules)
{fw_bug_summary}

---

## Service Connection Configs

Each service's `services/<name>/connection.json` lists its upstream dependencies.
The `upstreams` section must reference the **correct** DNS hostname and port from
`config/dns.json`. After fixing DNS, regenerate or update each connection config
so `dns_name` and `port` values are consistent with `config/dns.json`.

---

## Fix Procedure

1. **Fix `config/dns.json`**:
   - Restore any missing service entries.
   - Correct hostnames that point to wrong hosts.
   - Correct port numbers that are off.
   - Correct protocol values (`http` vs `https`).

2. **Fix `config/firewall.json`**:
   - Add missing allow rules for required edges.
   - Do NOT use wildcard sources or destinations.
   - Do NOT change the `default_action` (must remain `deny`).

3. **Fix `services/<svc>/connection.json`**:
   - Update `dns_name` and `port` in each upstream entry to match corrected DNS.

4. **Validate**:
   - Run `python3 tests/test_connectivity.py` — all tests must pass.
   - Produce `attestation.json` with `verdict="pass"`.

---

## Constraints

- Do NOT allow all traffic (no wildcard rules).
- Do NOT change service names or port assignments (use the values in this spec).
- All {len(services)} services must be reachable via correct DNS entries.
- `config/services.json` is the source of truth for host/port — do not modify it.
"""


def _generate_brief(services: list, svc_count: int) -> str:
    return f"""# INC4: DNS / Routing Misconfiguration (Brief)

Several microservices are failing to communicate. Alerts show repeated connection
refused and name resolution errors across the cluster.

**Services involved** ({svc_count} total):
{chr(10).join(f"- `{svc}`" for svc in services)}

**Workspace structure**:
- `config/services.json` — service registry (source of truth, do not modify)
- `config/dns.json` — DNS table mapping services to hostname/port/protocol
- `config/firewall.json` — firewall allow-list for service-to-service traffic
- `services/<name>/connection.json` — per-service upstream connection config
- `tests/test_connectivity.py` — connectivity validation tests

**Goal**: Diagnose and fix the networking configuration so all required
service-to-service communication paths work correctly.

**What to do**:
1. Inspect `config/dns.json` for incorrect hostnames, ports, or protocols.
2. Inspect `config/firewall.json` for missing allow rules.
3. Update `services/<svc>/connection.json` to reflect corrected DNS entries.
4. Run `python3 tests/test_connectivity.py` to verify all connectivity tests pass.

The Planner has the full network topology diagram, the correct DNS entries,
the correct firewall rules, and the port mappings. Coordinate with the Planner
before making changes.

**Constraint**: Do not add wildcard/permissive firewall rules that allow all traffic.
"""
