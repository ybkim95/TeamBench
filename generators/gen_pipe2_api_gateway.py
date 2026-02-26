"""
Parameterized generator for PIPE2: API Gateway Routing Fix.

Each seed produces:
  - A different set of 3-5 backend services
  - 8-15 routes with varying patterns (path prefixes, rewrites, auth methods, rate limits)
  - Deliberate bugs injected into gateway/config.json:
      * wrong_upstream: route points to the wrong service
      * missing_rewrite: path_rewrite is absent or incorrect
      * wrong_auth: auth method doesn't match spec
      * missing_rate_limit: rate_limit_tier is absent or wrong
  - gateway/router.py: a Python gateway router that reads config.json
  - services/: mock backend service definitions
  - tests/test_routes.py: route tests that pass only when config is correct

TNI Design (Pattern D — Cross-System Contract):
  - Brief: "The API gateway has misconfigured routing. Some requests are failing. Fix the configuration."
  - Spec (Planner-visible): complete routing table with upstreams, path rewrites,
    per-route auth method, rate limit tier, health-check paths, service discovery.
  - Executor sees: broken config.json, router.py, service stubs, failing tests.
  - Without the Planner's routing table the Executor cannot know correct upstreams/rewrites.
"""
from __future__ import annotations

import json
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Service catalogue ─────────────────────────────────────────────────────────

SERVICE_SETS = [
    {
        "services": [
            {"name": "user-service",     "host": "users.internal",    "port": 8001, "health": "/health"},
            {"name": "order-service",    "host": "orders.internal",   "port": 8002, "health": "/healthz"},
            {"name": "product-service",  "host": "products.internal", "port": 8003, "health": "/ping"},
            {"name": "payment-service",  "host": "payments.internal", "port": 8004, "health": "/health"},
            {"name": "notify-service",   "host": "notify.internal",   "port": 8005, "health": "/status"},
        ],
        "routes": [
            # (path_prefix, upstream_service, strip_prefix, path_rewrite, auth, rate_tier)
            ("/api/v1/users",        "user-service",    True,  "/users",         "jwt",     "standard"),
            ("/api/v1/orders",       "order-service",   True,  "/orders",        "jwt",     "standard"),
            ("/api/v1/products",     "product-service", True,  "/products",      "api_key", "high"),
            ("/api/v1/payments",     "payment-service", True,  "/payments",      "oauth2",  "low"),
            ("/api/v1/notifications","notify-service",  True,  "/notifications", "jwt",     "standard"),
            ("/api/v1/users/me",     "user-service",    True,  "/users/profile", "jwt",     "high"),
            ("/api/v1/orders/bulk",  "order-service",   True,  "/orders/batch",  "oauth2",  "low"),
            ("/api/v1/products/search","product-service",True, "/search",        "none",    "high"),
            ("/api/v1/payments/webhook","payment-service",True,"/webhook",       "none",    "low"),
            ("/health",              "user-service",    False, "/health",        "none",    "none"),
        ],
    },
    {
        "services": [
            {"name": "auth-service",     "host": "auth.internal",     "port": 9001, "health": "/health"},
            {"name": "catalog-service",  "host": "catalog.internal",  "port": 9002, "health": "/ping"},
            {"name": "cart-service",     "host": "cart.internal",     "port": 9003, "health": "/healthz"},
            {"name": "review-service",   "host": "reviews.internal",  "port": 9004, "health": "/health"},
        ],
        "routes": [
            ("/v2/auth",             "auth-service",    True,  "/",              "none",    "high"),
            ("/v2/auth/refresh",     "auth-service",    True,  "/refresh",       "jwt",     "high"),
            ("/v2/catalog",          "catalog-service", True,  "/items",         "api_key", "standard"),
            ("/v2/catalog/search",   "catalog-service", True,  "/items/search",  "none",    "high"),
            ("/v2/cart",             "cart-service",    True,  "/cart",          "jwt",     "standard"),
            ("/v2/cart/checkout",    "cart-service",    True,  "/cart/checkout", "oauth2",  "low"),
            ("/v2/reviews",          "review-service",  True,  "/reviews",       "api_key", "standard"),
            ("/v2/reviews/submit",   "review-service",  True,  "/reviews/new",   "jwt",     "standard"),
            ("/v2/admin/catalog",    "catalog-service", True,  "/admin/items",   "oauth2",  "low"),
            ("/healthcheck",         "auth-service",    False, "/health",        "none",    "none"),
        ],
    },
    {
        "services": [
            {"name": "inventory-service","host": "inventory.internal", "port": 7001, "health": "/health"},
            {"name": "shipping-service", "host": "shipping.internal",  "port": 7002, "health": "/ping"},
            {"name": "pricing-service",  "host": "pricing.internal",   "port": 7003, "health": "/healthz"},
            {"name": "report-service",   "host": "reports.internal",   "port": 7004, "health": "/health"},
            {"name": "webhook-service",  "host": "webhooks.internal",  "port": 7005, "health": "/status"},
        ],
        "routes": [
            ("/api/inventory",       "inventory-service","True", "/stock",        "jwt",     "standard"),
            ("/api/inventory/bulk",  "inventory-service","True", "/stock/batch",  "oauth2",  "low"),
            ("/api/shipping",        "shipping-service", "True", "/shipments",    "api_key", "standard"),
            ("/api/shipping/track",  "shipping-service", "True", "/track",        "none",    "high"),
            ("/api/pricing",         "pricing-service",  "True", "/prices",       "jwt",     "high"),
            ("/api/pricing/quote",   "pricing-service",  "True", "/quote",        "none",    "high"),
            ("/api/reports",         "report-service",   "True", "/generate",     "oauth2",  "low"),
            ("/api/reports/export",  "report-service",   "True", "/export",       "oauth2",  "low"),
            ("/api/webhooks",        "webhook-service",  "True", "/receive",      "none",    "low"),
            ("/ping",                "inventory-service","False","/health",       "none",    "none"),
            ("/api/pricing/bulk",    "pricing-service",  "True", "/prices/batch", "jwt",     "standard"),
        ],
    },
    {
        "services": [
            {"name": "account-service",  "host": "accounts.internal",  "port": 6001, "health": "/health"},
            {"name": "media-service",    "host": "media.internal",     "port": 6002, "health": "/ping"},
            {"name": "search-service",   "host": "search.internal",    "port": 6003, "health": "/healthz"},
            {"name": "feed-service",     "host": "feed.internal",      "port": 6004, "health": "/health"},
        ],
        "routes": [
            ("/api/accounts",        "account-service", True,  "/accounts",      "jwt",     "standard"),
            ("/api/accounts/signup", "account-service", True,  "/signup",        "none",    "high"),
            ("/api/accounts/login",  "account-service", True,  "/login",         "none",    "high"),
            ("/api/media/upload",    "media-service",   True,  "/upload",        "jwt",     "low"),
            ("/api/media/download",  "media-service",   True,  "/download",      "api_key", "high"),
            ("/api/search",          "search-service",  True,  "/query",         "none",    "high"),
            ("/api/search/suggest",  "search-service",  True,  "/suggest",       "none",    "high"),
            ("/api/feed",            "feed-service",    True,  "/feed",          "jwt",     "standard"),
            ("/api/feed/trending",   "feed-service",    True,  "/trending",      "none",    "high"),
            ("/api/admin/accounts",  "account-service", True,  "/admin",         "oauth2",  "low"),
            ("/status",              "account-service", False, "/health",        "none",    "none"),
            ("/api/media/metadata",  "media-service",   True,  "/metadata",      "jwt",     "standard"),
        ],
    },
]

# Rate limit tiers (requests/minute)
RATE_LIMIT_TIERS = {
    "low":      {"requests_per_minute": 10,  "burst": 5},
    "standard": {"requests_per_minute": 100, "burst": 20},
    "high":     {"requests_per_minute": 500, "burst": 100},
    "none":     {"requests_per_minute": 0,   "burst": 0},  # no rate limit (health/public)
}

# Bug type definitions: (bug_key, description)
BUG_TYPES = [
    "wrong_upstream",
    "missing_rewrite",
    "wrong_auth",
    "missing_rate_limit",
]


def _pick_wrong_service(correct_service: str, all_services: list[dict], rng: SeededRandom) -> str:
    """Pick a different service name to use as a wrong upstream."""
    others = [s["name"] for s in all_services if s["name"] != correct_service]
    return rng.choice(others) if others else correct_service + "-wrong"


def _pick_wrong_auth(correct_auth: str, rng: SeededRandom) -> str:
    """Pick a different auth method."""
    all_auths = ["jwt", "api_key", "oauth2", "none"]
    others = [a for a in all_auths if a != correct_auth]
    return rng.choice(others)


def _pick_wrong_tier(correct_tier: str, rng: SeededRandom) -> str:
    """Pick a different rate limit tier."""
    all_tiers = ["low", "standard", "high"]
    others = [t for t in all_tiers if t != correct_tier]
    return rng.choice(others) if others else "standard"


class Generator(TaskGenerator):
    task_id = "PIPE2_api_gateway"
    domain = "pipeline"
    difficulty = "medium"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Select service/route set
        sset = SERVICE_SETS[seed % len(SERVICE_SETS)]
        services = sset["services"]
        route_templates = sset["routes"]

        # Build correct routing table
        correct_routes = []
        for tpl in route_templates:
            path_prefix, upstream, strip_prefix, path_rewrite, auth, rate_tier = tpl
            svc = next((s for s in services if s["name"] == upstream), services[0])
            correct_routes.append({
                "path_prefix":   path_prefix,
                "upstream":      upstream,
                "upstream_host": svc["host"],
                "upstream_port": svc["port"],
                "strip_prefix":  bool(strip_prefix),
                "path_rewrite":  path_rewrite,
                "auth":          auth,
                "rate_limit_tier": rate_tier,
            })

        # Decide which routes get bugs: inject 3-5 bugs across distinct routes
        # (never bug the health/public "none" routes to keep tests sensible)
        injectable_idxs = [
            i for i, r in enumerate(correct_routes)
            if r["rate_limit_tier"] != "none"
        ]
        num_bugs = min(rng.randint(3, 5), len(injectable_idxs))
        bug_idxs = rng.sample(injectable_idxs, num_bugs)

        # Cycle through bug types
        bugs_assigned: list[tuple[int, str]] = []
        for i, idx in enumerate(bug_idxs):
            bug_type = BUG_TYPES[i % len(BUG_TYPES)]
            bugs_assigned.append((idx, bug_type))

        # Build buggy routes for config.json
        buggy_routes = []
        bug_manifest = {}  # route_path -> {bug_type, original, injected}
        for i, route in enumerate(correct_routes):
            buggy = dict(route)
            # Find if this index has a bug
            my_bugs = [bt for (idx, bt) in bugs_assigned if idx == i]
            if my_bugs:
                bug_type = my_bugs[0]
                if bug_type == "wrong_upstream":
                    wrong_svc_name = _pick_wrong_service(route["upstream"], services, rng)
                    wrong_svc = next((s for s in services if s["name"] == wrong_svc_name), services[0])
                    buggy["upstream"] = wrong_svc_name
                    buggy["upstream_host"] = wrong_svc["host"]
                    buggy["upstream_port"] = wrong_svc["port"]
                    bug_manifest[route["path_prefix"]] = {
                        "bug_type": "wrong_upstream",
                        "field": "upstream",
                        "correct": route["upstream"],
                        "injected": wrong_svc_name,
                    }
                elif bug_type == "missing_rewrite":
                    # Give an incorrect path rewrite (missing leading slash or wrong path)
                    wrong_rewrite = route["path_rewrite"].rstrip("/") + "/v2"
                    buggy["path_rewrite"] = wrong_rewrite
                    bug_manifest[route["path_prefix"]] = {
                        "bug_type": "missing_rewrite",
                        "field": "path_rewrite",
                        "correct": route["path_rewrite"],
                        "injected": wrong_rewrite,
                    }
                elif bug_type == "wrong_auth":
                    wrong_auth = _pick_wrong_auth(route["auth"], rng)
                    buggy["auth"] = wrong_auth
                    bug_manifest[route["path_prefix"]] = {
                        "bug_type": "wrong_auth",
                        "field": "auth",
                        "correct": route["auth"],
                        "injected": wrong_auth,
                    }
                elif bug_type == "missing_rate_limit":
                    wrong_tier = _pick_wrong_tier(route["rate_limit_tier"], rng)
                    buggy["rate_limit_tier"] = wrong_tier
                    bug_manifest[route["path_prefix"]] = {
                        "bug_type": "missing_rate_limit",
                        "field": "rate_limit_tier",
                        "correct": route["rate_limit_tier"],
                        "injected": wrong_tier,
                    }
            buggy_routes.append(buggy)

        # Build expected dict for grader
        expected = {
            "services": services,
            "correct_routes": correct_routes,
            "bug_manifest": bug_manifest,
            "rate_limit_tiers": RATE_LIMIT_TIERS,
        }

        # Build workspace files
        workspace_files = {}

        # gateway/config.json  — intentionally buggy
        gateway_config = {
            "gateway": {
                "listen_port": 8080,
                "service_discovery": {
                    "type": "static",
                    "refresh_interval_sec": 30,
                },
            },
            "services": {
                svc["name"]: {
                    "host": svc["host"],
                    "port": svc["port"],
                    "health_check_path": svc["health"],
                }
                for svc in services
            },
            "rate_limit_tiers": RATE_LIMIT_TIERS,
            "routes": [
                {
                    "path_prefix":    r["path_prefix"],
                    "upstream":       r["upstream"],
                    "strip_prefix":   r["strip_prefix"],
                    "path_rewrite":   r["path_rewrite"],
                    "auth":           r["auth"],
                    "rate_limit_tier": r["rate_limit_tier"],
                }
                for r in buggy_routes
            ],
        }
        workspace_files["gateway/config.json"] = json.dumps(gateway_config, indent=2)

        # gateway/router.py
        workspace_files["gateway/router.py"] = self._generate_router()

        # services/  — one stub per service
        for svc in services:
            workspace_files[f"services/{svc['name']}.json"] = json.dumps({
                "name":         svc["name"],
                "host":         svc["host"],
                "port":         svc["port"],
                "health_path":  svc["health"],
                "description":  f"Mock definition for {svc['name']}",
            }, indent=2)

        # tests/test_routes.py
        workspace_files["tests/test_routes.py"] = self._generate_tests(
            correct_routes, services
        )

        # spec and brief
        spec_md = self._generate_spec(services, correct_routes, bug_manifest)
        brief_md = self._generate_brief(services)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── File generators ───────────────────────────────────────────────────────

    def _generate_router(self) -> str:
        return '''\
"""
API Gateway Router.

Reads gateway/config.json and provides routing logic.
The router matches incoming request paths to routes, enforces auth,
applies rate limits, and rewrites paths before forwarding to upstreams.

Fix gateway/config.json so that all routes are correctly configured.
Do NOT modify this file.
"""
import json
import os
from dataclasses import dataclass
from typing import Optional


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


@dataclass
class RouteMatch:
    upstream: str
    upstream_host: str
    upstream_port: int
    rewritten_path: str
    auth: str
    rate_limit_tier: str


def load_config(config_path: str = CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_route(
    request_path: str,
    config: dict,
) -> Optional[RouteMatch]:
    """
    Match a request path to the first matching route (longest-prefix wins).
    Returns None if no route matches.
    """
    routes = config.get("routes", [])
    services = config.get("services", {})

    # Sort by prefix length descending so most-specific wins
    sorted_routes = sorted(routes, key=lambda r: len(r["path_prefix"]), reverse=True)

    for route in sorted_routes:
        prefix = route["path_prefix"]
        if request_path == prefix or request_path.startswith(prefix + "/") or request_path.startswith(prefix + "?"):
            upstream_name = route["upstream"]
            svc = services.get(upstream_name)
            if svc is None:
                return None  # upstream not found in service registry

            strip = route.get("strip_prefix", True)
            rewrite = route.get("path_rewrite", "")
            if strip and rewrite:
                suffix = request_path[len(prefix):]
                rewritten = rewrite.rstrip("/") + suffix if suffix else rewrite
            else:
                rewritten = request_path

            return RouteMatch(
                upstream=upstream_name,
                upstream_host=svc["host"],
                upstream_port=svc["port"],
                rewritten_path=rewritten,
                auth=route.get("auth", "none"),
                rate_limit_tier=route.get("rate_limit_tier", "standard"),
            )

    return None


def get_health_check_path(service_name: str, config: dict) -> Optional[str]:
    """Return the health check path for a given service."""
    svc = config.get("services", {}).get(service_name)
    if svc:
        return svc.get("health_check_path")
    return None


def get_rate_limit(tier: str, config: dict) -> dict:
    """Return rate limit settings for a given tier."""
    tiers = config.get("rate_limit_tiers", {})
    return tiers.get(tier, {"requests_per_minute": 0, "burst": 0})


if __name__ == "__main__":
    cfg = load_config()
    print(f"Loaded {len(cfg[\'routes\'])} routes, {len(cfg[\'services\'])} services")
    # Quick smoke test
    for route in cfg["routes"][:3]:
        match = resolve_route(route["path_prefix"], cfg)
        if match:
            print(f"  {route[\'path_prefix\']} -> {match.upstream}:{match.upstream_port}{match.rewritten_path} [{match.auth}]")
        else:
            print(f"  {route[\'path_prefix\']} -> NO MATCH")
'''

    def _generate_tests(self, correct_routes: list[dict], services: list[dict]) -> str:
        """Generate tests/test_routes.py that pass only with correct config."""

        # Build test cases from correct routes
        test_cases = []
        for route in correct_routes:
            test_cases.append({
                "path":         route["path_prefix"],
                "upstream":     route["upstream"],
                "path_rewrite": route["path_rewrite"],
                "auth":         route["auth"],
                "rate_tier":    route["rate_limit_tier"],
            })

        test_cases_json = json.dumps(test_cases, indent=4)
        service_names = [s["name"] for s in services]
        service_names_json = json.dumps(service_names)

        header = (
            '"""\n'
            "Route tests for the API gateway.\n"
            "\n"
            "These tests load gateway/config.json via the router and verify that:\n"
            "- Each route resolves to the correct upstream service\n"
            "- Each route applies the correct path rewrite\n"
            "- Each route enforces the correct auth method\n"
            "- Each route uses the correct rate limit tier\n"
            "- Health check paths are accessible\n"
            "- All configured service names exist in the service registry\n"
            "\n"
            "Tests PASS only when gateway/config.json is correctly configured.\n"
            'Fix gateway/config.json (not this file) to make them pass.\n'
            '"""\n'
            "import json\n"
            "import os\n"
            "import sys\n"
            "import pytest\n"
            "\n"
            "# Make gateway/ importable from workspace root\n"
            'sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))\n'
            "from gateway.router import load_config, resolve_route, get_health_check_path, get_rate_limit\n"
            "\n"
            'CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "gateway", "config.json")\n'
            "\n"
            f"EXPECTED_ROUTES = {test_cases_json}\n"
            "\n"
            f"EXPECTED_SERVICES = {service_names_json}\n"
        )
        return header + r'''


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


# ── Test 1: Config loads successfully ─────────────────────────────────────────
def test_config_loads(config):
    assert "routes" in config, "config.json must have a 'routes' key"
    assert "services" in config, "config.json must have a 'services' key"
    assert len(config["routes"]) > 0, "routes list must not be empty"


# ── Test 2: All expected services are registered ──────────────────────────────
def test_all_services_registered(config):
    for svc_name in EXPECTED_SERVICES:
        assert svc_name in config["services"], (
            f"Service {svc_name!r} missing from config.json services registry"
        )


# ── Test 3: Each route resolves to the correct upstream ───────────────────────
def test_route_upstreams(config):
    for tc in EXPECTED_ROUTES:
        match = resolve_route(tc["path"], config)
        assert match is not None, (
            f"Route {tc['path']!r} did not resolve to any upstream"
        )
        assert match.upstream == tc["upstream"], (
            f"Route {tc['path']!r}: upstream should be {tc['upstream']!r}, "
            f"got {match.upstream!r}"
        )


# ── Test 4: Each route applies the correct path rewrite ───────────────────────
def test_route_path_rewrites(config):
    for tc in EXPECTED_ROUTES:
        match = resolve_route(tc["path"], config)
        if match is None:
            continue
        assert match.rewritten_path == tc["path_rewrite"], (
            f"Route {tc['path']!r}: path_rewrite should be {tc['path_rewrite']!r}, "
            f"got {match.rewritten_path!r}"
        )


# ── Test 5: Each route enforces the correct auth method ───────────────────────
def test_route_auth_methods(config):
    for tc in EXPECTED_ROUTES:
        match = resolve_route(tc["path"], config)
        if match is None:
            continue
        assert match.auth == tc["auth"], (
            f"Route {tc['path']!r}: auth should be {tc['auth']!r}, "
            f"got {match.auth!r}"
        )


# ── Test 6: Each route has the correct rate limit tier ────────────────────────
def test_route_rate_limits(config):
    for tc in EXPECTED_ROUTES:
        match = resolve_route(tc["path"], config)
        if match is None:
            continue
        assert match.rate_limit_tier == tc["rate_tier"], (
            f"Route {tc['path']!r}: rate_limit_tier should be {tc['rate_tier']!r}, "
            f"got {match.rate_limit_tier!r}"
        )


# ── Test 7: Health check paths are set for all services ───────────────────────
def test_health_check_paths(config):
    for svc_name in EXPECTED_SERVICES:
        hc = get_health_check_path(svc_name, config)
        assert hc is not None, (
            f"Service {svc_name!r} is missing health_check_path"
        )
        assert hc.startswith("/"), (
            f"Service {svc_name!r} health_check_path must start with /, got {hc!r}"
        )


# ── Test 8: Rate limit tier definitions exist for all used tiers ──────────────
def test_rate_limit_tiers_defined(config):
    used_tiers = {r["rate_limit_tier"] for r in config["routes"]}
    for tier in used_tiers:
        rl = get_rate_limit(tier, config)
        assert "requests_per_minute" in rl, (
            f"Rate limit tier {tier!r} missing 'requests_per_minute'"
        )
        assert "burst" in rl, (
            f"Rate limit tier {tier!r} missing 'burst'"
        )


# ── Test 9: No route points to an unregistered service ────────────────────────
def test_no_dangling_upstreams(config):
    registered = set(config.get("services", {}).keys())
    for route in config["routes"]:
        assert route["upstream"] in registered, (
            f"Route {route['path_prefix']!r} references unknown upstream "
            f"{route['upstream']!r} (not in services registry)"
        )


# ── Test 10: Longest-prefix match works correctly ─────────────────────────────
def test_longest_prefix_match(config):
    """More specific routes must win over less specific ones."""
    for tc in EXPECTED_ROUTES:
        match = resolve_route(tc["path"], config)
        assert match is not None, f"No match for {tc['path']!r}"
        assert match.upstream == tc["upstream"], (
            f"Longest-prefix mismatch on {tc['path']!r}: "
            f"expected {tc['upstream']!r}, got {match.upstream!r}"
        )


# ── Test 11: Path suffix is preserved after rewrite ──────────────────────────
def test_path_suffix_preservation(config):
    """Paths with suffixes beyond the prefix must have suffix appended after rewrite."""
    for tc in EXPECTED_ROUTES:
        base = tc["path"]
        suffix = "/extra"
        match = resolve_route(base + suffix, config)
        if match is None:
            continue
        # Rewritten path should end with the suffix
        assert match.rewritten_path.endswith(suffix) or match.rewritten_path == tc["path_rewrite"], (
            f"Suffix not preserved: {base + suffix!r} -> {match.rewritten_path!r}"
        )


if __name__ == "__main__":
    import subprocess, sys
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
'''

    def _generate_spec(
        self,
        services: list[dict],
        correct_routes: list[dict],
        bug_manifest: dict,
    ) -> str:
        """Full spec for Planner — contains the complete correct routing table."""

        # Service table
        svc_rows = "\n".join(
            f"| `{s['name']}` | `{s['host']}` | `{s['port']}` | `{s['health']}` |"
            for s in services
        )

        # Route table
        route_rows = "\n".join(
            f"| `{r['path_prefix']}` | `{r['upstream']}` | `{r['path_rewrite']}` "
            f"| `{r['auth']}` | `{r['rate_limit_tier']}` | {'yes' if r['strip_prefix'] else 'no'} |"
            for r in correct_routes
        )

        # Rate limit table
        rl_rows = "\n".join(
            f"| `{tier}` | {info['requests_per_minute']} | {info['burst']} |"
            for tier, info in RATE_LIMIT_TIERS.items()
        )

        # Bug summary
        bug_lines = []
        for path, info in bug_manifest.items():
            bug_lines.append(
                f"- `{path}`: **{info['bug_type']}** — "
                f"field `{info['field']}` is `{info['injected']!r}`, "
                f"should be `{info['correct']!r}`"
            )
        bug_section = "\n".join(bug_lines) if bug_lines else "_(none)_"

        return f"""# PIPE2: API Gateway Routing Fix — Planner Specification

## Situation

The API gateway's `gateway/config.json` contains deliberate routing errors.
The Executor can see the broken config but does NOT know what the correct routes
should be. Your job as Planner is to relay the complete correct routing table
so the Executor can fix the config.

---

## Service Registry

The gateway routes requests to the following backend services:

| Service Name | Host | Port | Health Check Path |
|---|---|---|---|
{svc_rows}

All services must appear in `config.json` under the `services` key with their
`host`, `port`, and `health_check_path` fields.

---

## Complete Correct Routing Table

The gateway must implement exactly these routes:

| Path Prefix | Upstream Service | Path Rewrite | Auth Method | Rate Limit Tier | Strip Prefix |
|---|---|---|---|---|---|
{route_rows}

### Column Definitions

- **Path Prefix**: Incoming request path prefix to match (longest-prefix wins)
- **Upstream Service**: Backend service name (must exist in services registry)
- **Path Rewrite**: The path sent to the upstream after stripping the prefix
- **Auth Method**: `jwt`, `api_key`, `oauth2`, or `none`
- **Rate Limit Tier**: See rate limit table below
- **Strip Prefix**: Whether to remove the path prefix before rewriting

---

## Rate Limit Tier Definitions

| Tier | Requests per Minute | Burst |
|---|---|---|
{rl_rows}

---

## Auth Method Semantics

- `none`: No authentication required (public endpoints, health checks)
- `jwt`: Bearer JWT token required in `Authorization` header
- `api_key`: API key required in `X-API-Key` header
- `oauth2`: OAuth 2.0 access token required

---

## Bugs Injected into config.json

The following errors are present in the current `gateway/config.json` and must be corrected:

{bug_section}

---

## Deliverables

The Executor must fix `gateway/config.json` so that:

1. Every route's `upstream` points to the correct service name
2. Every route's `path_rewrite` matches the spec exactly
3. Every route's `auth` matches the spec exactly
4. Every route's `rate_limit_tier` matches the spec exactly
5. All services are present in the `services` registry with correct host/port/health path
6. All rate limit tier definitions are present
7. `pytest tests/test_routes.py` passes with zero failures

**Do not modify `gateway/router.py` or `tests/test_routes.py`.**
"""

    def _generate_brief(self, services: list[dict]) -> str:
        """Brief for Executor — describes the problem WITHOUT the routing table."""
        svc_names = ", ".join(f"`{s['name']}`" for s in services)
        return f"""# PIPE2: API Gateway Routing Fix (Brief)

## Situation

The API gateway is misconfigured. Several routes in `gateway/config.json` have
errors: wrong upstream services, incorrect path rewrites, wrong auth requirements,
and incorrect rate limit tiers.

**The Planner has the complete correct routing table.** Coordinate with the Planner
to get the correct upstream, path rewrite, auth method, and rate limit for each route.

## What You Have

- `gateway/config.json` — gateway configuration with deliberate errors
- `gateway/router.py` — gateway router (reads config.json; do NOT modify)
- `services/` — mock backend service definitions ({svc_names})
- `tests/test_routes.py` — route tests (do NOT modify)

## What's Wrong

Some routes in `gateway/config.json` have:
- Wrong `upstream` (pointing to the wrong backend service)
- Wrong `path_rewrite` (requests forwarded to the wrong upstream path)
- Wrong `auth` (incorrect authentication method required)
- Wrong `rate_limit_tier` (incorrect rate limiting applied)

## What You Must Produce

Fix `gateway/config.json` so that:
1. `pytest tests/test_routes.py` passes with zero failures
2. Each route points to the correct upstream service
3. Each route has the correct path rewrite
4. Each route enforces the correct auth method
5. Each route uses the correct rate limit tier

**Do not modify `gateway/router.py` or `tests/test_routes.py`.**
Ask the Planner for the correct routing table.
"""
