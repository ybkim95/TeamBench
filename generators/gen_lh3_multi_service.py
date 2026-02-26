"""
Parameterized generator for LH3: Multi-Service Bug Fix.

Each seed produces:
- Different service topology (chain A→B→C, fan-out A→{B,C,D}, diamond A→{B,C}→D)
- Different service types (api, worker, gateway)
- Different bug distributions (one bug per service, two bugs in one service)
- Different bug types per service (wrong endpoint URL, wrong response field name,
  missing error handling, wrong HTTP method, wrong content type)
- 3-4 service directories each with server.py + config.json
- Spec with full service interaction diagram and correct contracts
- Brief that is intentionally vague

TNI Pattern D,F:
- Spec (seen by Planner/Verifier): complete service dependency graph, correct contracts,
  which service has which bug, expected data flow
- Brief (seen by Executor): vague "the system is broken, fix it"
"""
from __future__ import annotations

import json
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Topology definitions ──────────────────────────────────────────────────────

TOPOLOGIES = [
    {
        "name": "chain",
        "description": "Linear chain: A → B → C",
        "services": ["service_a", "service_b", "service_c"],
        "edges": [("service_a", "service_b"), ("service_b", "service_c")],
        "entry": "service_a",
        "diagram": "service_a → service_b → service_c",
    },
    {
        "name": "fan_out",
        "description": "Fan-out: A calls B, C, D in parallel",
        "services": ["service_a", "service_b", "service_c", "service_d"],
        "edges": [("service_a", "service_b"), ("service_a", "service_c"), ("service_a", "service_d")],
        "entry": "service_a",
        "diagram": "service_a → {service_b, service_c, service_d}",
    },
    {
        "name": "diamond",
        "description": "Diamond: A calls B and C, both call D",
        "services": ["service_a", "service_b", "service_c", "service_d"],
        "edges": [("service_a", "service_b"), ("service_a", "service_c"),
                  ("service_b", "service_d"), ("service_c", "service_d")],
        "entry": "service_a",
        "diagram": "service_a → {service_b, service_c} → service_d",
    },
]

# ── Service type configs ──────────────────────────────────────────────────────

SERVICE_TYPE_POOL = [
    {"type": "api",     "port_base": 8000, "description": "REST API service"},
    {"type": "worker",  "port_base": 8100, "description": "Background worker service"},
    {"type": "gateway", "port_base": 8200, "description": "API gateway service"},
    {"type": "store",   "port_base": 8300, "description": "Data store service"},
]

# ── Bug type definitions ──────────────────────────────────────────────────────

# Each bug type: (name, description, correct_value_key, wrong_value_key)
BUG_TYPES = [
    "wrong_endpoint_url",
    "wrong_response_field",
    "missing_error_handling",
    "wrong_http_method",
    "wrong_content_type",
]

# Endpoint URL pairs: (correct_path, wrong_path)
ENDPOINT_URL_VARIANTS = [
    ("/api/process",  "/api/proc"),
    ("/api/store",    "/api/save"),
    ("/api/validate", "/api/check"),
    ("/api/transform","/api/convert"),
    ("/api/forward",  "/api/relay"),
    ("/api/aggregate","/api/collect"),
]

# Response field name pairs: (correct_field, wrong_field)
RESPONSE_FIELD_VARIANTS = [
    ("result",  "data"),
    ("payload", "body"),
    ("output",  "response"),
    ("value",   "result"),
    ("status",  "state"),
    ("records", "items"),
]

# HTTP method pairs: (correct_method, wrong_method)
HTTP_METHOD_VARIANTS = [
    ("POST", "GET"),
    ("POST", "PUT"),
    ("PUT",  "POST"),
    ("GET",  "POST"),
]

# Content type pairs: (correct_ct, wrong_ct)
CONTENT_TYPE_VARIANTS = [
    ("application/json", "text/plain"),
    ("application/json", "application/x-www-form-urlencoded"),
    ("application/json", "text/html"),
]

# Domain themes for service naming
DOMAIN_THEMES = [
    {
        "domain": "payments",
        "nouns": ["Payment", "Transaction", "Charge", "Invoice", "Receipt"],
        "verbs": ["process", "validate", "store", "forward", "aggregate"],
        "data_field": "amount",
        "id_field": "payment_id",
    },
    {
        "domain": "orders",
        "nouns": ["Order", "Item", "Shipment", "Fulfillment", "Delivery"],
        "verbs": ["process", "validate", "store", "route", "confirm"],
        "data_field": "total",
        "id_field": "order_id",
    },
    {
        "domain": "events",
        "nouns": ["Event", "Log", "Metric", "Alert", "Report"],
        "verbs": ["ingest", "validate", "store", "aggregate", "forward"],
        "data_field": "payload",
        "id_field": "event_id",
    },
    {
        "domain": "users",
        "nouns": ["User", "Profile", "Session", "Token", "Permission"],
        "verbs": ["create", "validate", "store", "enrich", "sync"],
        "data_field": "user_data",
        "id_field": "user_id",
    },
    {
        "domain": "inventory",
        "nouns": ["Product", "Stock", "Warehouse", "Catalog", "Reserve"],
        "verbs": ["check", "reserve", "store", "update", "release"],
        "data_field": "quantity",
        "id_field": "product_id",
    },
]


class Generator(TaskGenerator):
    task_id = "LH3_multi_service"
    domain = "operations"
    difficulty = "expert"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pick topology
        topo = TOPOLOGIES[seed % len(TOPOLOGIES)]

        # Pick domain theme
        theme = DOMAIN_THEMES[seed % len(DOMAIN_THEMES)]

        # Assign service types to each service
        num_services = len(topo["services"])
        type_indices = rng.sample(list(range(len(SERVICE_TYPE_POOL))), min(num_services, len(SERVICE_TYPE_POOL)))
        while len(type_indices) < num_services:
            type_indices.append(rng.randint(0, len(SERVICE_TYPE_POOL) - 1))
        svc_types = [SERVICE_TYPE_POOL[i] for i in type_indices[:num_services]]

        # Assign ports deterministically
        ports = {}
        for i, svc_name in enumerate(topo["services"]):
            ports[svc_name] = svc_types[i]["port_base"] + i

        # Pick bug distribution: "one_per_service" or "two_in_one"
        bug_dist = rng.choice(["one_per_service", "two_in_one"])

        # Assign bugs
        bugs = self._assign_bugs(rng, topo["services"], bug_dist)

        # Pick correct endpoint URLs for all edges
        edge_contracts = {}
        for caller, callee in topo["edges"]:
            ep_idx = rng.randint(0, len(ENDPOINT_URL_VARIANTS) - 1)
            rf_idx = rng.randint(0, len(RESPONSE_FIELD_VARIANTS) - 1)
            edge_contracts[(caller, callee)] = {
                "correct_endpoint": ENDPOINT_URL_VARIANTS[ep_idx][0],
                "wrong_endpoint":   ENDPOINT_URL_VARIANTS[ep_idx][1],
                "correct_field":    RESPONSE_FIELD_VARIANTS[rf_idx][0],
                "wrong_field":      RESPONSE_FIELD_VARIANTS[rf_idx][1],
                "correct_method":   "POST",
                "wrong_method":     rng.choice(["GET", "PUT"]),
                "correct_ct":       "application/json",
                "wrong_ct":         rng.choice(["text/plain", "application/x-www-form-urlencoded"]),
            }

        # Generate workspace files
        workspace_files = self._build_workspace(topo, theme, svc_types, ports, bugs, edge_contracts, rng)

        # Compute expected
        expected = {
            "topology": topo["name"],
            "domain": theme["domain"],
            "num_services": num_services,
            "bug_distribution": bug_dist,
            "bugs": {svc: info for svc, info in bugs.items()},
            "ports": ports,
            "edge_contracts": {
                f"{caller}_to_{callee}": contract
                for (caller, callee), contract in edge_contracts.items()
            },
        }

        spec_md = self._generate_spec(topo, theme, svc_types, ports, bugs, edge_contracts)
        brief_md = self._generate_brief(topo, theme)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── Bug assignment ────────────────────────────────────────────────────────

    def _assign_bugs(self, rng: SeededRandom, services: list[str], bug_dist: str) -> dict:
        """
        Assign bugs to services.

        one_per_service: each service gets exactly one bug (uses first N services if >3)
        two_in_one: one service gets 2 bugs, remaining services get one each
        """
        bugs = {}
        available_bug_types = list(BUG_TYPES)
        rng.shuffle(available_bug_types)

        if bug_dist == "one_per_service":
            # Every service gets one bug; rotate through bug types
            for i, svc in enumerate(services):
                bugs[svc] = {
                    "type": available_bug_types[i % len(available_bug_types)],
                    "count": 1,
                }
        else:
            # "two_in_one": pick a random service to have 2 bugs
            double_svc_idx = rng.randint(0, len(services) - 1)
            for i, svc in enumerate(services):
                if i == double_svc_idx:
                    b1 = available_bug_types[i % len(available_bug_types)]
                    b2 = available_bug_types[(i + 1) % len(available_bug_types)]
                    bugs[svc] = {"types": [b1, b2], "count": 2}
                else:
                    bugs[svc] = {
                        "type": available_bug_types[(i + 2) % len(available_bug_types)],
                        "count": 1,
                    }

        return bugs

    # ── Workspace builder ─────────────────────────────────────────────────────

    def _build_workspace(
        self,
        topo: dict,
        theme: dict,
        svc_types: list,
        ports: dict,
        bugs: dict,
        edge_contracts: dict,
        rng: SeededRandom,
    ) -> dict[str, str]:
        files = {}

        # Build each service directory
        for i, svc_name in enumerate(topo["services"]):
            svc_type = svc_types[i]
            port = ports[svc_name]
            svc_bugs = bugs[svc_name]

            # Determine which services this service calls
            callees = [callee for (caller, callee) in topo["edges"] if caller == svc_name]

            # Generate config.json
            config = {
                "service_name": svc_name,
                "service_type": svc_type["type"],
                "port": port,
                "upstream_services": {
                    callee: {
                        "host": "localhost",
                        "port": ports[callee],
                        "base_url": f"http://localhost:{ports[callee]}",
                    }
                    for callee in callees
                },
                "timeout_seconds": 10,
                "retry_attempts": 3,
            }
            files[f"{svc_name}/config.json"] = json.dumps(config, indent=2)

            # Generate server.py with injected bugs
            server_py = self._generate_server(
                svc_name, svc_type, port, callees, ports, theme,
                svc_bugs, edge_contracts, topo,
            )
            files[f"{svc_name}/server.py"] = server_py

        # Generate integration test runner
        files["run_integration_test.py"] = self._generate_integration_test(
            topo, theme, ports, edge_contracts,
        )

        # Generate README with run instructions
        files["README.md"] = self._generate_readme(topo, theme, ports)

        return files

    def _generate_server(
        self,
        svc_name: str,
        svc_type: dict,
        port: int,
        callees: list[str],
        ports: dict,
        theme: dict,
        svc_bugs: dict,
        edge_contracts: dict,
        topo: dict,
    ) -> str:
        """Generate a server.py for one service, injecting the appropriate bugs."""

        # Determine bug types for this service
        if svc_bugs.get("count", 1) == 2:
            bug_type_list = svc_bugs.get("types", ["wrong_endpoint_url", "missing_error_handling"])
        else:
            bug_type_list = [svc_bugs.get("type", "wrong_endpoint_url")]

        has_bug = lambda b: b in bug_type_list  # noqa: E731

        # Build upstream call snippets
        upstream_calls = []
        for callee in callees:
            contract = edge_contracts.get((svc_name, callee), {})
            correct_ep = contract.get("correct_endpoint", "/api/process")
            wrong_ep   = contract.get("wrong_endpoint",   "/api/proc")
            correct_f  = contract.get("correct_field",    "result")
            wrong_f    = contract.get("wrong_field",      "data")
            correct_m  = contract.get("correct_method",   "POST")
            wrong_m    = contract.get("wrong_method",     "GET")
            correct_ct = contract.get("correct_ct",       "application/json")
            wrong_ct   = contract.get("wrong_ct",         "text/plain")

            callee_port = ports[callee]

            # Inject bugs into upstream call
            endpoint_used = wrong_ep   if has_bug("wrong_endpoint_url") else correct_ep
            method_used   = wrong_m    if has_bug("wrong_http_method")  else correct_m
            ct_used       = wrong_ct   if has_bug("wrong_content_type") else correct_ct
            field_used    = wrong_f    if has_bug("wrong_response_field") else correct_f

            if has_bug("missing_error_handling"):
                # Missing try/except around the upstream call
                call_snippet = f"""
    # Call {callee}
    upstream_url = f"http://localhost:{callee_port}{endpoint_used}"
    resp = _http_post(upstream_url, data, headers={{"Content-Type": "{ct_used}"}}, method="{method_used}")
    upstream_result = resp.get("{field_used}", None)
    upstream_results["{callee}"] = upstream_result
"""
            else:
                call_snippet = f"""
    # Call {callee}
    try:
        upstream_url = f"http://localhost:{callee_port}{endpoint_used}"
        resp = _http_post(upstream_url, data, headers={{"Content-Type": "{ct_used}"}}, method="{method_used}")
        if resp is None:
            return {{"error": "upstream_{callee}_unavailable", "service": "{svc_name}"}}, 503
        upstream_result = resp.get("{field_used}", None)
        upstream_results["{callee}"] = upstream_result
    except Exception as exc:
        return {{"error": f"upstream_{callee}_error: {{exc}}", "service": "{svc_name}"}}, 500
"""
            upstream_calls.append(call_snippet)

        upstream_section = "".join(upstream_calls) if upstream_calls else ""

        # Determine if this is a leaf service (no callees)
        is_leaf = len(callees) == 0
        data_field = theme["data_field"]
        id_field   = theme["id_field"]

        if is_leaf:
            process_body = f"""
    # Leaf service: store/process the data
    record_id = data.get("{id_field}", "unknown")
    value = data.get("{data_field}", None)
    # Simulate storage
    _store[record_id] = value
    return {{"result": "stored", "record_id": record_id, "stored_value": value}}, 200
"""
        else:
            process_body = f"""{upstream_section}
    # Combine upstream results and pass through
    record_id = data.get("{id_field}", "unknown")
    value = data.get("{data_field}", None)
    return {{
        "result": "processed",
        "record_id": record_id,
        "{data_field}": value,
        "upstream": upstream_results,
    }}, 200
"""

        return f'''"""
{svc_name}: {svc_type["description"]}
Service type: {svc_type["type"]}
Port: {port}
"""
import json
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

# In-memory store (leaf services)
_store = {{}}


def _http_post(url, data, headers=None, method="POST"):
    """Make an HTTP request to an upstream service."""
    headers = headers or {{}}
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {{"error": e.reason, "status": e.code}}
    except urllib.error.URLError as e:
        return None


def process(data):
    """
    Main processing logic for {svc_name}.
    Calls upstream services and returns combined result.
    """
    upstream_results = {{}}
{process_body}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress default access log

    def do_POST(self):
        if self.path == "/api/process":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._respond(400, {{"error": "invalid_json"}})
                return
            result, status = process(data)
            self._respond(status, result)
        elif self.path == "/health":
            self._respond(200, {{"service": "{svc_name}", "status": "ok"}})
        else:
            self._respond(404, {{"error": "not_found", "path": self.path}})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {{"service": "{svc_name}", "status": "ok"}})
        else:
            self._respond(404, {{"error": "not_found", "path": self.path}})

    def _respond(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    port = {port}
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"{svc_name} listening on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    def _generate_integration_test(
        self,
        topo: dict,
        theme: dict,
        ports: dict,
        edge_contracts: dict,
    ) -> str:
        entry = topo["entry"]
        entry_port = ports[entry]
        data_field = theme["data_field"]
        id_field   = theme["id_field"]

        return f'''"""
Integration test for the {theme["domain"]} microservice system.
Tests the full data flow through the service topology: {topo["diagram"]}

Run AFTER starting all services. Checks end-to-end correctness.
Usage: python run_integration_test.py
"""
import json
import sys
import subprocess
import time
import urllib.request
import urllib.error


SERVICES = {json.dumps([
    {"name": svc, "port": ports[svc]}
    for svc in topo["services"]
], indent=4)}

ENTRY_PORT = {entry_port}
ENTRY_SERVICE = "{entry}"

PASS = 0
FAIL = 0
FAILURES = []


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS: {{name}}")
        PASS += 1
    else:
        print(f"  FAIL: {{name}}{{(' - ' + detail) if detail else ''}}")
        FAIL += 1
        FAILURES.append(name)


def http_post(url, data, timeout=5):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={{"Content-Type": "application/json"}},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {{}}
    except Exception as e:
        return None, str(e)


def http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {{}}
    except Exception as e:
        return None, str(e)


def wait_for_service(port, name, retries=10):
    for _ in range(retries):
        try:
            status, _ = http_get(f"http://localhost:{{port}}/health")
            if status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    print("=== Integration Test: {theme["domain"].title()} Microservice System ===")
    print(f"Topology: {topo["diagram"]}")
    print()

    # 1. Health checks for all services
    print("--- Health Checks ---")
    for svc in SERVICES:
        reachable = wait_for_service(svc["port"], svc["name"], retries=5)
        check(f"{{svc[\'name\']}} health", reachable, f"port {{svc[\'port\']}}")

    print()
    print("--- End-to-End Data Flow ---")

    # 2. Send a test request through the entry service
    test_payload = {{
        "{id_field}": "test-001",
        "{data_field}": 42,
    }}
    status, resp = http_post(
        f"http://localhost:{{ENTRY_PORT}}/api/process",
        test_payload,
    )
    check("entry service responds", status is not None, f"status={{status}}")
    check("entry service returns 200", status == 200, f"got {{status}}")
    check("response has result field", isinstance(resp, dict) and "result" in resp,
          f"response: {{resp}}")

    # 3. Check that data flows correctly (result must be non-error)
    if isinstance(resp, dict):
        check("no error in response", "error" not in resp,
              resp.get("error", ""))
        check("record_id echoed correctly",
              resp.get("record_id") == "test-001" or "upstream" in resp,
              f"resp keys: {{list(resp.keys())}}")

    # 4. Test with a second payload to verify consistency
    test_payload2 = {{
        "{id_field}": "test-002",
        "{data_field}": 99,
    }}
    status2, resp2 = http_post(
        f"http://localhost:{{ENTRY_PORT}}/api/process",
        test_payload2,
    )
    check("second request succeeds", status2 == 200, f"got {{status2}}")

    # 5. Error handling: send malformed JSON check
    print()
    print("--- Error Handling ---")
    status_err, resp_err = http_post(
        f"http://localhost:{{ENTRY_PORT}}/api/process",
        {{"bad_key": "no_required_fields"}},
    )
    # Should still return 200 or a graceful error, not crash
    check("handles missing fields gracefully",
          status_err in (200, 400, 422),
          f"got {{status_err}}")

    # 6. Verify each service responds to health endpoint
    print()
    print("--- Individual Service Health ---")
    for svc in SERVICES:
        s, r = http_get(f"http://localhost:{{svc[\'port\']}}/health")
        check(f"{{svc[\'name\']}} /health returns 200", s == 200)
        check(f"{{svc[\'name\']}} reports correct name",
              isinstance(r, dict) and r.get("service") == svc["name"],
              f"got: {{r}}")

    # Summary
    total = PASS + FAIL
    partial = round(PASS / max(1, total), 2)
    print()
    print(f"=== Results: {{PASS}}/{{total}} passed (partial={{partial}}) ===")
    if FAILURES:
        print(f"Failures: {{FAILURES}}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
'''

    def _generate_readme(self, topo: dict, theme: dict, ports: dict) -> str:
        svc_lines = "\n".join(
            f"  python {svc}/server.py &"
            for svc in topo["services"]
        )
        return f"""# {theme["domain"].title()} Microservice System

## Topology
{topo["diagram"]}

## Services
{chr(10).join(f"- **{svc}**: port {port}" for svc, port in ports.items())}

## Running the System

Start all services (each in background):
```bash
{svc_lines}
```

Run the integration test:
```bash
python run_integration_test.py
```

## Known Issues
The system is currently broken. Fix all bugs so the integration test passes.
"""

    # ── Spec and Brief ────────────────────────────────────────────────────────

    def _generate_spec(
        self,
        topo: dict,
        theme: dict,
        svc_types: list,
        ports: dict,
        bugs: dict,
        edge_contracts: dict,
    ) -> str:
        domain = theme["domain"]
        data_field = theme["data_field"]
        id_field = theme["id_field"]
        services = topo["services"]

        # Build service table
        svc_rows = []
        for i, svc in enumerate(services):
            svc_rows.append(
                f"| {svc} | {svc_types[i]['type']} | {ports[svc]} | "
                f"{svc_types[i]['description']} |"
            )
        svc_table = "\n".join(svc_rows)

        # Build edge contract table
        edge_rows = []
        for (caller, callee), contract in edge_contracts.items():
            edge_rows.append(
                f"| {caller} → {callee} | POST | {contract['correct_endpoint']} | "
                f"application/json | `{contract['correct_field']}` |"
            )
        edge_table = "\n".join(edge_rows)

        # Build bug description section
        bug_sections = []
        for svc in services:
            svc_bug = bugs[svc]
            if svc_bug.get("count", 1) == 2:
                types_str = " and ".join(svc_bug.get("types", []))
                bug_sections.append(
                    f"- **{svc}**: Has 2 bugs — `{types_str}`\n"
                    + self._bug_fix_hint(svc, svc_bug.get("types", []), edge_contracts, topo)
                )
            else:
                bt = svc_bug.get("type", "unknown")
                bug_sections.append(
                    f"- **{svc}**: Has 1 bug — `{bt}`\n"
                    + self._bug_fix_hint(svc, [bt], edge_contracts, topo)
                )
        bug_section_text = "\n".join(bug_sections)

        return f"""# LH3: Multi-Service Bug Fix — {domain.title()} System

## Goal
Fix all bugs across the {len(services)}-service {domain} system so that the
end-to-end integration test (`python run_integration_test.py`) passes completely.

## System Topology

```
{topo["diagram"]}
```

**Topology type**: {topo["name"]} ({topo["description"]})

## Service Inventory

| Service | Type | Port | Description |
|---------|------|------|-------------|
{svc_table}

## Service Interaction Contracts

Every inter-service call must use these exact contracts:

| Edge | Method | Endpoint | Content-Type | Response Field |
|------|--------|----------|--------------|----------------|
{edge_table}

### Data Schema

All services pass the following payload shape:
```json
{{
  "{id_field}": "<string>",
  "{data_field}": "<value>"
}}
```

Response shape from intermediate services:
```json
{{
  "result": "processed",
  "record_id": "<string>",
  "{data_field}": "<value>",
  "upstream": {{ ... }}
}}
```

Response shape from leaf services:
```json
{{
  "result": "stored",
  "record_id": "<string>",
  "stored_value": "<value>"
}}
```

## Bug Inventory

The following bugs are present in the system. Each service has a specific bug
that breaks the data flow. Fix **all** bugs:

{bug_section_text}

## Error Handling Requirements

- Every upstream call MUST be wrapped in try/except
- Upstream failures must return HTTP 503 with `{{"error": "upstream_<service>_unavailable"}}`
- Invalid JSON in request body must return HTTP 400
- Unknown routes must return HTTP 404

## Grading Criteria

1. All services start without errors (each service independently runnable)
2. Health endpoint `/health` responds 200 on all services
3. Correct HTTP method on all inter-service calls
4. Correct endpoint URL on all inter-service calls
5. Correct Content-Type header on all inter-service calls
6. Correct response field name read from upstream responses
7. All upstream calls wrapped in try/except error handling
8. End-to-end POST to entry service returns 200 with correct structure
9. `record_id` and `{data_field}` propagate through the pipeline
10. Second request also succeeds (no state corruption)
11. Malformed/missing fields handled gracefully (no 5xx crashes)
12. No new bugs introduced (existing correct logic not broken)

## Deliverables
- Fixed `<service>/server.py` for each service that has a bug
- All {len(services)} services must pass health checks
- `python run_integration_test.py` must exit 0
"""

    def _bug_fix_hint(
        self,
        svc_name: str,
        bug_types: list[str],
        edge_contracts: dict,
        topo: dict,
    ) -> str:
        hints = []
        # Find the edge where this service is the caller
        callee_contracts = {
            callee: contract
            for (caller, callee), contract in edge_contracts.items()
            if caller == svc_name
        }

        for bt in bug_types:
            if bt == "wrong_endpoint_url":
                for callee, c in callee_contracts.items():
                    hints.append(
                        f"  - In `{svc_name}/server.py`: the URL used to call `{callee}` "
                        f"is `{c['wrong_endpoint']}` but must be `{c['correct_endpoint']}`"
                    )
            elif bt == "wrong_response_field":
                for callee, c in callee_contracts.items():
                    hints.append(
                        f"  - In `{svc_name}/server.py`: reads `resp.get(\"{c['wrong_field']}\")` "
                        f"from `{callee}` response but must read `\"{c['correct_field']}\"`"
                    )
            elif bt == "missing_error_handling":
                hints.append(
                    f"  - In `{svc_name}/server.py`: upstream calls are not wrapped in try/except; "
                    f"add error handling that returns 503 on upstream failure"
                )
            elif bt == "wrong_http_method":
                for callee, c in callee_contracts.items():
                    hints.append(
                        f"  - In `{svc_name}/server.py`: uses HTTP `{c['wrong_method']}` "
                        f"to call `{callee}` but must use `{c['correct_method']}`"
                    )
            elif bt == "wrong_content_type":
                for callee, c in callee_contracts.items():
                    hints.append(
                        f"  - In `{svc_name}/server.py`: sends Content-Type `{c['wrong_ct']}` "
                        f"to `{callee}` but must send `{c['correct_ct']}`"
                    )

        return "\n".join(hints) if hints else "  - See server.py for details"

    def _generate_brief(self, topo: dict, theme: dict) -> str:
        return f"""# LH3: Multi-Service Bug Fix (Brief)

The {theme["domain"]} microservice system is broken.

Services: {", ".join(topo["services"])}
Topology: {topo["diagram"]}

The system has failures. Investigate each service, find all bugs, and fix them
so that the end-to-end integration test passes.

Start all services, then run: `python run_integration_test.py`

The Planner has the full service interaction diagram and knows exactly which
service has which bug.
"""
