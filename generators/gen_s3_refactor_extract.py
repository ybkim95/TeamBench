"""
Parameterized generator for S3: Refactor Extract.

TNI Pattern D (Cross-System Contract):
  - Spec has: exact architecture diagram showing which functions/classes go into
    which new modules, public API contracts, import dependency rules.
  - Brief says: "The main application file is too large. Refactor it for better
    maintainability."
  - TNI driver: Without the Planner's architecture diagram the Executor has no way
    to determine WHERE to split or what the module boundaries must be.

Each seed produces a different:
  - Application type (web_api / data_pipeline / cli_tool)
  - Module names and function/class assignments
  - Dependency patterns between extracted modules
  - File and function naming conventions
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Application type variants ────────────────────────────────────────────────

APP_TYPES = ["web_api", "data_pipeline", "cli_tool"]

# ── Web API name pools ───────────────────────────────────────────────────────

WEB_RESOURCE_NAMES = [
    ("users", "products", "orders"),
    ("articles", "comments", "tags"),
    ("employees", "departments", "projects"),
    ("customers", "invoices", "payments"),
    ("posts", "categories", "media"),
    ("events", "attendees", "venues"),
]

WEB_APP_NAMES = [
    "shop_api", "blog_api", "hr_api", "billing_api",
    "cms_api", "events_api", "inventory_api", "tracker_api",
]

# ── Data pipeline name pools ─────────────────────────────────────────────────

PIPELINE_STAGE_SETS = [
    ("ingest", "transform", "validate", "export"),
    ("extract", "clean", "enrich", "load"),
    ("fetch", "normalize", "aggregate", "publish"),
    ("read", "filter", "compute", "write"),
]

PIPELINE_APP_NAMES = [
    "etl_pipeline", "data_processor", "stream_handler",
    "batch_runner", "report_builder", "sync_worker",
]

# ── CLI tool name pools ──────────────────────────────────────────────────────

CLI_COMMAND_SETS = [
    ("init", "build", "deploy", "status"),
    ("create", "list", "update", "delete"),
    ("scan", "report", "fix", "verify"),
    ("start", "stop", "restart", "logs"),
]

CLI_APP_NAMES = [
    "devctl", "svcmgr", "projctl", "infra_cli",
    "admin_tool", "deploy_cli", "audit_cli", "ops_tool",
]

# ── Complexity patterns: inter-module dependency wiring ──────────────────────
# Each entry is a list of (importer_module_idx, importee_module_idx) pairs.
# Indices into the list of extracted modules.

DEPENDENCY_PATTERNS = [
    # Pattern A: linear chain  0->1->2->3 (main uses all)
    [(1, 0), (2, 1), (3, 2)],
    # Pattern B: star  main uses all, no inter-module deps
    [],
    # Pattern C: two independent pairs  (0,1) and (2,3)
    [(1, 0), (3, 2)],
    # Pattern D: diamond  main->0,1  0->2  1->2
    [(1, 0), (2, 1), (2, 0)],   # module indices for extracted set only
]


# ── Generator ────────────────────────────────────────────────────────────────

class Generator(TaskGenerator):
    task_id = "S3_refactor_extract"
    domain = "software"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pin app_type by seed index so seeds 0,1,2 always produce all three variants.
        # Within each variant the rng drives all sub-choices (names, stages, commands).
        app_type = APP_TYPES[seed % len(APP_TYPES)]

        if app_type == "web_api":
            return self._generate_web_api(seed, rng)
        elif app_type == "data_pipeline":
            return self._generate_data_pipeline(seed, rng)
        else:
            return self._generate_cli_tool(seed, rng)

    # ── Web API variant ──────────────────────────────────────────────────────

    def _generate_web_api(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        app_name = rng.choice(WEB_APP_NAMES)
        r1, r2, r3 = rng.choice(WEB_RESOURCE_NAMES)
        dep_pattern = rng.choice(DEPENDENCY_PATTERNS)

        # Extracted modules: models, routes, utils  (always 3 for web_api)
        modules = ["models", "routes", "utils"]

        # Build monolith
        monolith = self._build_web_monolith(app_name, r1, r2, r3)
        test_file = self._build_web_tests(app_name, r1, r2, r3)

        spec_md = self._web_spec(app_name, r1, r2, r3, modules)
        brief_md = self._web_brief(app_name)

        expected = {
            "app_type": "web_api",
            "app_name": app_name,
            "monolith_file": "app.py",
            "modules": modules,
            "resource_names": [r1, r2, r3],
            "module_contents": {
                "models": [
                    f"{r1.rstrip('s').capitalize()}",
                    f"{r2.rstrip('s').capitalize()}",
                    f"{r3.rstrip('s').capitalize()}",
                ],
                "routes": [
                    f"get_{r1}", f"create_{r1.rstrip('s')}",
                    f"get_{r2}", f"create_{r2.rstrip('s')}",
                    f"get_{r3}", f"create_{r3.rstrip('s')}",
                ],
                "utils": ["validate_id", "format_response", "paginate"],
            },
            "public_apis": {
                "models": [f"{r1.rstrip('s').capitalize()}", f"{r2.rstrip('s').capitalize()}", f"{r3.rstrip('s').capitalize()}"],
                "routes": [f"get_{r1}", f"create_{r1.rstrip('s')}", f"get_{r2}", f"create_{r2.rstrip('s')}", f"get_{r3}", f"create_{r3.rstrip('s')}"],
                "utils": ["validate_id", "format_response", "paginate"],
            },
            "import_rules": "routes imports from models and utils; models is standalone; utils is standalone",
            "no_circular_imports": True,
        }

        workspace_files = {
            "app.py": monolith,
            "tests/test_app.py": test_file,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _build_web_monolith(self, app_name: str, r1: str, r2: str, r3: str) -> str:
        s1 = r1.rstrip("s").capitalize()
        s2 = r2.rstrip("s").capitalize()
        s3 = r3.rstrip("s").capitalize()
        return f'''"""
{app_name} - monolithic application module.

This single file contains models, route handlers, and utility functions
for managing {r1}, {r2}, and {r3}.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
import json
import re


# ============================================================
# MODELS
# ============================================================

class {s1}:
    """Represents a {r1.rstrip("s")} resource."""

    def __init__(self, id: int, name: str, **kwargs):
        self.id = id
        self.name = name
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        return {{"id": self.id, "name": self.name, **self.extra}}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{s1}":
        return cls(**data)

    def __repr__(self) -> str:
        return f"{s1}(id={{self.id}}, name={{self.name!r}})"


class {s2}:
    """Represents a {r2.rstrip("s")} resource."""

    def __init__(self, id: int, title: str, **kwargs):
        self.id = id
        self.title = title
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        return {{"id": self.id, "title": self.title, **self.extra}}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{s2}":
        return cls(**data)

    def __repr__(self) -> str:
        return f"{s2}(id={{self.id}}, title={{self.title!r}})"


class {s3}:
    """Represents a {r3.rstrip("s")} resource."""

    def __init__(self, id: int, ref: str, amount: float = 0.0, **kwargs):
        self.id = id
        self.ref = ref
        self.amount = amount
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        return {{"id": self.id, "ref": self.ref, "amount": self.amount, **self.extra}}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{s3}":
        return cls(**data)

    def __repr__(self) -> str:
        return f"{s3}(id={{self.id}}, ref={{self.ref!r}})"


# ============================================================
# UTILITIES
# ============================================================

def validate_id(value: Any) -> bool:
    """Return True if value is a positive integer."""
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def format_response(data: Any, status: int = 200) -> Dict[str, Any]:
    """Wrap data in a standard API response envelope."""
    return {{"status": status, "data": data}}


def paginate(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """Return a paginated slice of items."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return {{
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": max(1, (total + per_page - 1) // per_page),
    }}


# ============================================================
# ROUTE HANDLERS
# ============================================================

# In-memory stores (for demonstration)
_{r1}_store: List[{s1}] = []
_{r2}_store: List[{s2}] = []
_{r3}_store: List[{s3}] = []


def get_{r1}(page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """Return paginated list of {r1}."""
    items = [x.to_dict() for x in _{r1}_store]
    return format_response(paginate(items, page, per_page))


def create_{r1.rstrip("s")}(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new {r1.rstrip("s")} and return it."""
    if not validate_id(data.get("id")):
        return format_response({{"error": "invalid id"}}, status=400)
    obj = {s1}.from_dict(data)
    _{r1}_store.append(obj)
    return format_response(obj.to_dict(), status=201)


def get_{r2}(page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """Return paginated list of {r2}."""
    items = [x.to_dict() for x in _{r2}_store]
    return format_response(paginate(items, page, per_page))


def create_{r2.rstrip("s")}(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new {r2.rstrip("s")} and return it."""
    if not validate_id(data.get("id")):
        return format_response({{"error": "invalid id"}}, status=400)
    obj = {s2}.from_dict(data)
    _{r2}_store.append(obj)
    return format_response(obj.to_dict(), status=201)


def get_{r3}(page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """Return paginated list of {r3}."""
    items = [x.to_dict() for x in _{r3}_store]
    return format_response(paginate(items, page, per_page))


def create_{r3.rstrip("s")}(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new {r3.rstrip("s")} and return it."""
    if not validate_id(data.get("id")):
        return format_response({{"error": "invalid id"}}, status=400)
    obj = {s3}.from_dict(data)
    _{r3}_store.append(obj)
    return format_response(obj.to_dict(), status=201)
'''

    def _build_web_tests(self, app_name: str, r1: str, r2: str, r3: str) -> str:
        s1 = r1.rstrip("s").capitalize()
        s2 = r2.rstrip("s").capitalize()
        s3 = r3.rstrip("s").capitalize()
        return f'''"""Tests for {app_name}.

These tests import from the *refactored* module structure:
  - models.{s1}, models.{s2}, models.{s3}
  - routes.get_{r1}, routes.create_{r1.rstrip("s")}
  - routes.get_{r2}, routes.create_{r2.rstrip("s")}
  - routes.get_{r3}, routes.create_{r3.rstrip("s")}
  - utils.validate_id, utils.format_response, utils.paginate
"""
import pytest


def test_models_importable():
    from models import {s1}, {s2}, {s3}
    assert {s1} is not None
    assert {s2} is not None
    assert {s3} is not None


def test_{r1.rstrip("s")}_model():
    from models import {s1}
    obj = {s1}(id=1, name="test")
    d = obj.to_dict()
    assert d["id"] == 1
    assert d["name"] == "test"
    obj2 = {s1}.from_dict({{"id": 2, "name": "other"}})
    assert obj2.id == 2


def test_{r2.rstrip("s")}_model():
    from models import {s2}
    obj = {s2}(id=1, title="hello")
    d = obj.to_dict()
    assert d["id"] == 1
    assert d["title"] == "hello"


def test_{r3.rstrip("s")}_model():
    from models import {s3}
    obj = {s3}(id=1, ref="REF-001", amount=99.5)
    d = obj.to_dict()
    assert d["ref"] == "REF-001"
    assert d["amount"] == 99.5


def test_utils_importable():
    from utils import validate_id, format_response, paginate
    assert callable(validate_id)
    assert callable(format_response)
    assert callable(paginate)


def test_validate_id():
    from utils import validate_id
    assert validate_id(1) is True
    assert validate_id(0) is False
    assert validate_id("abc") is False
    assert validate_id(-1) is False


def test_format_response():
    from utils import format_response
    r = format_response({{"key": "val"}})
    assert r["status"] == 200
    assert r["data"] == {{"key": "val"}}
    r2 = format_response({{}}, status=201)
    assert r2["status"] == 201


def test_paginate():
    from utils import paginate
    items = list(range(25))
    result = paginate(items, page=1, per_page=10)
    assert result["items"] == list(range(10))
    assert result["total"] == 25
    assert result["pages"] == 3
    result2 = paginate(items, page=3, per_page=10)
    assert result2["items"] == list(range(20, 25))


def test_routes_importable():
    from routes import (
        get_{r1}, create_{r1.rstrip("s")},
        get_{r2}, create_{r2.rstrip("s")},
        get_{r3}, create_{r3.rstrip("s")},
    )
    assert callable(get_{r1})
    assert callable(create_{r1.rstrip("s")})


def test_create_and_get_{r1}():
    import routes
    # Reset store
    routes._{r1}_store.clear()
    resp = routes.create_{r1.rstrip("s")}({{"id": 1, "name": "Alpha"}})
    assert resp["status"] == 201
    resp2 = routes.get_{r1}()
    assert resp2["data"]["total"] == 1


def test_create_{r1.rstrip("s")}_invalid_id():
    import routes
    routes._{r1}_store.clear()
    resp = routes.create_{r1.rstrip("s")}({{"id": -1, "name": "Bad"}})
    assert resp["status"] == 400


def test_create_and_get_{r2}():
    import routes
    routes._{r2}_store.clear()
    resp = routes.create_{r2.rstrip("s")}({{"id": 10, "title": "Beta"}})
    assert resp["status"] == 201
    resp2 = routes.get_{r2}()
    assert resp2["data"]["total"] == 1


def test_create_and_get_{r3}():
    import routes
    routes._{r3}_store.clear()
    resp = routes.create_{r3.rstrip("s")}({{"id": 5, "ref": "X-001", "amount": 42.0}})
    assert resp["status"] == 201
    resp2 = routes.get_{r3}()
    assert resp2["data"]["total"] == 1


def test_routes_use_models():
    """routes must import from models, not redefine classes."""
    import routes
    import models
    # The stores in routes should contain model instances
    routes._{r1}_store.clear()
    routes.create_{r1.rstrip("s")}({{"id": 99, "name": "Gamma"}})
    item = routes._{r1}_store[0]
    assert isinstance(item, models.{s1})


def test_no_circular_imports():
    """Importing all three modules must not raise ImportError."""
    import models
    import utils
    import routes
    assert True
'''

    def _web_spec(self, app_name: str, r1: str, r2: str, r3: str, modules: list) -> str:
        s1 = r1.rstrip("s").capitalize()
        s2 = r2.rstrip("s").capitalize()
        s3 = r3.rstrip("s").capitalize()
        return f"""# S3: Refactor Extract — {app_name}

## Goal

Split the monolithic `app.py` into three modules with clear responsibilities,
preserving all public APIs so that `tests/test_app.py` continues to pass.

## Target Architecture

```
{app_name}/
├── app.py            ← DELETE or leave as thin re-export (all logic moves out)
├── models.py         ← Classes only: {s1}, {s2}, {s3}
├── routes.py         ← Route handlers; imports from models and utils
├── utils.py          ← Pure helpers: validate_id, format_response, paginate
└── tests/
    └── test_app.py   ← Unchanged; imports from models / routes / utils
```

## Module Contracts

### `models.py`
- **Exports**: `{s1}`, `{s2}`, `{s3}`
- **No imports** from `routes` or `utils` (standalone)
- Each class retains `__init__`, `to_dict`, `from_dict`, `__repr__`

### `utils.py`
- **Exports**: `validate_id`, `format_response`, `paginate`
- **No imports** from `models` or `routes` (standalone)
- Function signatures must be preserved exactly

### `routes.py`
- **Exports**: `get_{r1}`, `create_{r1.rstrip("s")}`, `get_{r2}`, `create_{r2.rstrip("s")}`, `get_{r3}`, `create_{r3.rstrip("s")}`
- **Imports** `{s1}`, `{s2}`, `{s3}` from `models`
- **Imports** `validate_id`, `format_response`, `paginate` from `utils`
- In-memory stores `_{r1}_store`, `_{r2}_store`, `_{r3}_store` live here
- **No imports** from `routes` in `models` or `utils` (no circular deps)

## Import Dependency Rules

```
models  ←  routes  →  utils
(no edges between models and utils; neither imports routes)
```

## Hard Requirements

1. After refactoring `tests/test_app.py` must pass with `python -m pytest tests/ -q`.
2. Each of `models.py`, `utils.py`, `routes.py` must be independently importable.
3. No circular imports allowed.
4. All public function and class signatures must be preserved exactly.
5. Total line count across new modules must be within ±20% of original `app.py`.
6. `app.py` may be deleted or reduced to a thin re-export shim — grader does not import it.

## Deliverables

- `models.py`, `routes.py`, `utils.py` in workspace root.
- All tests passing.
"""

    def _web_brief(self, app_name: str) -> str:
        return f"""# S3: Refactor Extract (Brief)

The `app.py` file in `{app_name}` has grown too large and mixes concerns.

Refactor it for better maintainability. The Planner has the target architecture
and module boundary details.

Existing tests in `tests/test_app.py` must continue to pass after the refactor.
"""

    # ── Data pipeline variant ────────────────────────────────────────────────

    def _generate_data_pipeline(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        app_name = rng.choice(PIPELINE_APP_NAMES)
        stages = list(rng.choice(PIPELINE_STAGE_SETS))  # 4 stages

        monolith = self._build_pipeline_monolith(app_name, stages)
        test_file = self._build_pipeline_tests(app_name, stages)
        spec_md = self._pipeline_spec(app_name, stages)
        brief_md = self._pipeline_brief(app_name)

        # Module names = stage names
        expected = {
            "app_type": "data_pipeline",
            "app_name": app_name,
            "monolith_file": "main.py",
            "modules": stages,
            "module_contents": {s: [f"{s}_data", f"run_{s}"] for s in stages},
            "public_apis": {s: [f"run_{s}"] for s in stages},
            "import_rules": "linear chain: " + " -> ".join(stages),
            "no_circular_imports": True,
        }

        workspace_files = {
            "main.py": monolith,
            "tests/test_main.py": test_file,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _build_pipeline_monolith(self, app_name: str, stages: list) -> str:
        s0, s1, s2, s3 = stages
        return f'''"""
{app_name} — monolithic data pipeline.

All four pipeline stages live in this single file:
  {s0} -> {s1} -> {s2} -> {s3}
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import hashlib
import json


# ============================================================
# STAGE 0 — {s0.upper()}
# ============================================================

def {s0}_data(source: str) -> List[Dict[str, Any]]:
    """Simulate reading raw records from a source."""
    records = []
    for i in range(5):
        records.append({{
            "id": i,
            "source": source,
            "raw_value": f"raw_{{i}}_from_{{source}}",
            "checksum": hashlib.md5(f"{{source}}_{{i}}".encode()).hexdigest()[:8],
        }})
    return records


def run_{s0}(source: str = "default") -> List[Dict[str, Any]]:
    """Entry point for the {s0} stage."""
    data = {s0}_data(source)
    return data


# ============================================================
# STAGE 1 — {s1.upper()}
# ============================================================

def {s1}_data(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply transformations to raw records."""
    out = []
    for rec in records:
        out.append({{
            "id": rec["id"],
            "source": rec["source"],
            "value": rec["raw_value"].upper().strip(),
            "checksum": rec["checksum"],
            "stage": "{s1}",
        }})
    return out


def run_{s1}(source: str = "default") -> List[Dict[str, Any]]:
    """Entry point for the {s1} stage; calls {s0} internally."""
    raw = run_{s0}(source)
    return {s1}_data(raw)


# ============================================================
# STAGE 2 — {s2.upper()}
# ============================================================

def {s2}_data(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate records, drop any with missing fields."""
    required = {{"id", "source", "value", "checksum"}}
    valid = []
    for rec in records:
        if required.issubset(rec.keys()) and rec["value"]:
            rec["valid"] = True
            valid.append(rec)
    return valid


def run_{s2}(source: str = "default") -> List[Dict[str, Any]]:
    """Entry point for the {s2} stage; calls {s1} internally."""
    transformed = run_{s1}(source)
    return {s2}_data(transformed)


# ============================================================
# STAGE 3 — {s3.upper()}
# ============================================================

def {s3}_data(records: List[Dict[str, Any]], dest: str = "output") -> Dict[str, Any]:
    """Serialize validated records into output payload."""
    return {{
        "destination": dest,
        "count": len(records),
        "records": records,
        "status": "ok",
    }}


def run_{s3}(source: str = "default", dest: str = "output") -> Dict[str, Any]:
    """Entry point for the {s3} stage; calls {s2} internally."""
    validated = run_{s2}(source)
    return {s3}_data(validated, dest)


# ============================================================
# PIPELINE ORCHESTRATOR
# ============================================================

def run_pipeline(source: str = "default", dest: str = "output") -> Dict[str, Any]:
    """Run the full {s0}->{s1}->{s2}->{s3} pipeline."""
    return run_{s3}(source, dest)
'''

    def _build_pipeline_tests(self, app_name: str, stages: list) -> str:
        s0, s1, s2, s3 = stages
        return f'''"""Tests for {app_name}.

These tests import from the *refactored* module structure:
  - {s0}.run_{s0}, {s0}.{s0}_data
  - {s1}.run_{s1}, {s1}.{s1}_data
  - {s2}.run_{s2}, {s2}.{s2}_data
  - {s3}.run_{s3}, {s3}.{s3}_data
"""
import pytest


def test_all_stage_modules_importable():
    import {s0}
    import {s1}
    import {s2}
    import {s3}
    assert True


def test_{s0}_run():
    from {s0} import run_{s0}
    result = run_{s0}("testsrc")
    assert isinstance(result, list)
    assert len(result) == 5
    for rec in result:
        assert rec["source"] == "testsrc"
        assert "raw_value" in rec


def test_{s0}_data():
    from {s0} import {s0}_data
    recs = {s0}_data("src")
    assert len(recs) == 5
    assert all("checksum" in r for r in recs)


def test_{s1}_run():
    from {s1} import run_{s1}
    result = run_{s1}("testsrc")
    assert isinstance(result, list)
    assert len(result) == 5
    for rec in result:
        assert rec["stage"] == "{s1}"
        assert rec["value"] == rec["value"].upper()


def test_{s1}_data():
    from {s1} import {s1}_data
    raw = [{{"id": 0, "source": "x", "raw_value": "hello", "checksum": "abc"}}]
    out = {s1}_data(raw)
    assert out[0]["value"] == "HELLO"


def test_{s2}_run():
    from {s2} import run_{s2}
    result = run_{s2}("testsrc")
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(r.get("valid") is True for r in result)


def test_{s2}_data_drops_invalid():
    from {s2} import {s2}_data
    records = [
        {{"id": 1, "source": "s", "value": "V", "checksum": "c"}},
        {{"id": 2}},  # missing fields — should be dropped
    ]
    out = {s2}_data(records)
    assert len(out) == 1


def test_{s3}_run():
    from {s3} import run_{s3}
    result = run_{s3}("testsrc", "testdest")
    assert result["destination"] == "testdest"
    assert result["count"] == 5
    assert result["status"] == "ok"


def test_{s3}_data():
    from {s3} import {s3}_data
    records = [{{"id": 0, "value": "X", "source": "s", "checksum": "c", "valid": True}}]
    out = {s3}_data(records, "dest")
    assert out["count"] == 1
    assert out["records"] == records


def test_stage_chain_{s1}_uses_{s0}():
    """{s1} must import run_{s0} from {s0}, not redefine it."""
    import {s1}
    import {s0}
    # Both should produce same raw output when called with same source
    raw_direct = {s0}.run_{s0}("chain_test")
    transformed = {s1}.run_{s1}("chain_test")
    # Every transformed record id should match a raw record id
    raw_ids = {{r["id"] for r in raw_direct}}
    trans_ids = {{r["id"] for r in transformed}}
    assert raw_ids == trans_ids


def test_stage_chain_{s2}_uses_{s1}():
    from {s2} import run_{s2}
    from {s1} import run_{s1}
    t = run_{s1}("chain2")
    v = run_{s2}("chain2")
    assert len(v) <= len(t)


def test_full_pipeline_via_modules():
    from {s3} import run_{s3}
    result = run_{s3}("pipeline_test", "final_dest")
    assert result["status"] == "ok"
    assert result["count"] > 0


def test_no_circular_imports():
    import {s0}
    import {s1}
    import {s2}
    import {s3}
    assert True
'''

    def _pipeline_spec(self, app_name: str, stages: list) -> str:
        s0, s1, s2, s3 = stages
        return f"""# S3: Refactor Extract — {app_name}

## Goal

Split the monolithic `main.py` into four stage modules with a clear linear
pipeline structure, preserving all public APIs so that `tests/test_main.py`
continues to pass.

## Target Architecture

```
{app_name}/
├── main.py       ← DELETE or reduce to thin re-export shim
├── {s0}.py       ← Stage 0: raw {s0}
├── {s1}.py       ← Stage 1: {s1} (imports from {s0})
├── {s2}.py       ← Stage 2: {s2} (imports from {s1})
├── {s3}.py       ← Stage 3: {s3} (imports from {s2})
└── tests/
    └── test_main.py  ← Unchanged
```

## Module Contracts

### `{s0}.py`
- **Exports**: `{s0}_data(source: str) -> list`, `run_{s0}(source: str) -> list`
- **No imports** from other pipeline stages (source stage)

### `{s1}.py`
- **Exports**: `{s1}_data(records: list) -> list`, `run_{s1}(source: str) -> list`
- **Imports** `run_{s0}` from `{s0}`
- `run_{s1}` calls `run_{s0}` then `{s1}_data`

### `{s2}.py`
- **Exports**: `{s2}_data(records: list) -> list`, `run_{s2}(source: str) -> list`
- **Imports** `run_{s1}` from `{s1}`
- `run_{s2}` calls `run_{s1}` then `{s2}_data`

### `{s3}.py`
- **Exports**: `{s3}_data(records: list, dest: str) -> dict`, `run_{s3}(source: str, dest: str) -> dict`
- **Imports** `run_{s2}` from `{s2}`
- `run_{s3}` calls `run_{s2}` then `{s3}_data`

## Import Dependency Rules

```
{s0}  <-  {s1}  <-  {s2}  <-  {s3}
(strict linear chain — no skipped imports, no circular deps)
```

## Hard Requirements

1. `tests/test_main.py` must pass with `python -m pytest tests/ -q`.
2. Each stage module must be independently importable.
3. No circular imports.
4. All public function signatures preserved exactly.
5. Total line count across new modules must be within ±20% of original `main.py`.
6. `main.py` may be deleted or reduced to a shim.

## Deliverables

- `{s0}.py`, `{s1}.py`, `{s2}.py`, `{s3}.py` in workspace root.
- All tests passing.
"""

    def _pipeline_brief(self, app_name: str) -> str:
        return f"""# S3: Refactor Extract (Brief)

The `main.py` file in `{app_name}` has grown too large and mixes concerns.

Refactor it for better maintainability. The Planner has the target architecture
and module boundary details.

Existing tests in `tests/test_main.py` must continue to pass after the refactor.
"""

    # ── CLI tool variant ─────────────────────────────────────────────────────

    def _generate_cli_tool(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        app_name = rng.choice(CLI_APP_NAMES)
        commands = list(rng.choice(CLI_COMMAND_SETS))  # 4 commands

        monolith = self._build_cli_monolith(app_name, commands)
        test_file = self._build_cli_tests(app_name, commands)
        spec_md = self._cli_spec(app_name, commands)
        brief_md = self._cli_brief(app_name)

        expected = {
            "app_type": "cli_tool",
            "app_name": app_name,
            "monolith_file": "main.py",
            "modules": ["commands", "parsers", "formatters"],
            "module_contents": {
                "commands": [f"cmd_{c}" for c in commands],
                "parsers": [f"parse_{c}_args" for c in commands],
                "formatters": ["format_success", "format_error", "format_table"],
            },
            "public_apis": {
                "commands": [f"cmd_{c}" for c in commands],
                "parsers": [f"parse_{c}_args" for c in commands],
                "formatters": ["format_success", "format_error", "format_table"],
            },
            "import_rules": "commands imports from parsers and formatters; parsers and formatters are standalone",
            "no_circular_imports": True,
        }

        workspace_files = {
            "main.py": monolith,
            "tests/test_main.py": test_file,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _build_cli_monolith(self, app_name: str, commands: list) -> str:
        c0, c1, c2, c3 = commands
        return f'''"""
{app_name} — monolithic CLI tool.

This single file contains argument parsers, output formatters, and
command implementations for: {c0}, {c1}, {c2}, {c3}.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import sys


# ============================================================
# ARGUMENT PARSERS
# ============================================================

def parse_{c0}_args(argv: List[str]) -> Dict[str, Any]:
    """Parse arguments for the {c0} command."""
    args = {{"command": "{c0}", "verbose": False, "target": "default"}}
    i = 0
    while i < len(argv):
        if argv[i] in ("-v", "--verbose"):
            args["verbose"] = True
        elif argv[i] in ("-t", "--target") and i + 1 < len(argv):
            args["target"] = argv[i + 1]
            i += 1
        i += 1
    return args


def parse_{c1}_args(argv: List[str]) -> Dict[str, Any]:
    """Parse arguments for the {c1} command."""
    args = {{"command": "{c1}", "force": False, "output": "stdout"}}
    i = 0
    while i < len(argv):
        if argv[i] in ("-f", "--force"):
            args["force"] = True
        elif argv[i] in ("-o", "--output") and i + 1 < len(argv):
            args["output"] = argv[i + 1]
            i += 1
        i += 1
    return args


def parse_{c2}_args(argv: List[str]) -> Dict[str, Any]:
    """Parse arguments for the {c2} command."""
    args = {{"command": "{c2}", "dry_run": False, "env": "production"}}
    i = 0
    while i < len(argv):
        if argv[i] in ("-n", "--dry-run"):
            args["dry_run"] = True
        elif argv[i] in ("-e", "--env") and i + 1 < len(argv):
            args["env"] = argv[i + 1]
            i += 1
        i += 1
    return args


def parse_{c3}_args(argv: List[str]) -> Dict[str, Any]:
    """Parse arguments for the {c3} command."""
    args = {{"command": "{c3}", "format": "text", "filter": None}}
    i = 0
    while i < len(argv):
        if argv[i] in ("--json",):
            args["format"] = "json"
        elif argv[i] in ("--filter",) and i + 1 < len(argv):
            args["filter"] = argv[i + 1]
            i += 1
        i += 1
    return args


# ============================================================
# OUTPUT FORMATTERS
# ============================================================

def format_success(message: str, data: Any = None) -> str:
    """Format a success message, optionally including data."""
    parts = [f"[OK] {{message}}"]
    if data is not None:
        parts.append(json.dumps(data, indent=2))
    return "\\n".join(parts)


def format_error(message: str, code: int = 1) -> str:
    """Format an error message with an exit code hint."""
    return f"[ERROR] {{message}} (code={{code}})"


def format_table(rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    """Render rows as a plain-text table."""
    if not rows:
        return "(no data)"
    cols = columns or list(rows[0].keys())
    widths = {{c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    body = ["\\n".join(
        " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols)
        for r in rows
    )]
    return "\\n".join([header, sep] + body)


# ============================================================
# COMMAND IMPLEMENTATIONS
# ============================================================

def cmd_{c0}(argv: List[str]) -> str:
    """Execute the {c0} command."""
    args = parse_{c0}_args(argv)
    target = args["target"]
    verbose = args["verbose"]
    result = {{"command": "{c0}", "target": target, "status": "done"}}
    if verbose:
        result["detail"] = f"Completed {c0} on {{target}}"
    return format_success(f"{c0} completed for {{target}}", result if verbose else None)


def cmd_{c1}(argv: List[str]) -> str:
    """Execute the {c1} command."""
    args = parse_{c1}_args(argv)
    force = args["force"]
    output = args["output"]
    rows = [
        {{"item": "alpha", "status": "ready"}},
        {{"item": "beta", "status": "pending"}},
    ]
    table = format_table(rows)
    if output == "json":
        return format_success(f"{c1} results", rows)
    return format_success(f"{c1} output:\\n{{table}}")


def cmd_{c2}(argv: List[str]) -> str:
    """Execute the {c2} command."""
    args = parse_{c2}_args(argv)
    dry_run = args["dry_run"]
    env = args["env"]
    if dry_run:
        return format_success(f"[DRY RUN] would {c2} to {{env}}")
    return format_success(f"{c2} to {{env}} complete")


def cmd_{c3}(argv: List[str]) -> str:
    """Execute the {c3} command."""
    args = parse_{c3}_args(argv)
    fmt = args["format"]
    flt = args["filter"]
    data = [{{"key": "uptime", "value": "99.9%"}}, {{"key": "region", "value": "us-east"}}]
    if flt:
        data = [d for d in data if flt in str(d.get("value", ""))]
    if fmt == "json":
        return format_success("{c3} data", data)
    return format_success("{c3} output", format_table(data))
'''

    def _build_cli_tests(self, app_name: str, commands: list) -> str:
        c0, c1, c2, c3 = commands
        return f'''"""Tests for {app_name}.

These tests import from the *refactored* module structure:
  - commands.cmd_{c0}, cmd_{c1}, cmd_{c2}, cmd_{c3}
  - parsers.parse_{c0}_args, parse_{c1}_args, parse_{c2}_args, parse_{c3}_args
  - formatters.format_success, format_error, format_table
"""
import pytest


def test_all_modules_importable():
    import commands
    import parsers
    import formatters
    assert True


def test_parsers_importable():
    from parsers import (
        parse_{c0}_args, parse_{c1}_args,
        parse_{c2}_args, parse_{c3}_args,
    )
    assert callable(parse_{c0}_args)


def test_parse_{c0}_args_defaults():
    from parsers import parse_{c0}_args
    args = parse_{c0}_args([])
    assert args["command"] == "{c0}"
    assert args["verbose"] is False
    assert args["target"] == "default"


def test_parse_{c0}_args_flags():
    from parsers import parse_{c0}_args
    args = parse_{c0}_args(["-v", "--target", "myservice"])
    assert args["verbose"] is True
    assert args["target"] == "myservice"


def test_parse_{c1}_args_defaults():
    from parsers import parse_{c1}_args
    args = parse_{c1}_args([])
    assert args["command"] == "{c1}"
    assert args["force"] is False


def test_parse_{c1}_args_flags():
    from parsers import parse_{c1}_args
    args = parse_{c1}_args(["-f", "-o", "json"])
    assert args["force"] is True
    assert args["output"] == "json"


def test_parse_{c2}_args_defaults():
    from parsers import parse_{c2}_args
    args = parse_{c2}_args([])
    assert args["dry_run"] is False
    assert args["env"] == "production"


def test_parse_{c2}_args_flags():
    from parsers import parse_{c2}_args
    args = parse_{c2}_args(["-n", "-e", "staging"])
    assert args["dry_run"] is True
    assert args["env"] == "staging"


def test_parse_{c3}_args_defaults():
    from parsers import parse_{c3}_args
    args = parse_{c3}_args([])
    assert args["format"] == "text"
    assert args["filter"] is None


def test_formatters_importable():
    from formatters import format_success, format_error, format_table
    assert callable(format_success)
    assert callable(format_error)
    assert callable(format_table)


def test_format_success_no_data():
    from formatters import format_success
    out = format_success("done")
    assert "[OK]" in out
    assert "done" in out


def test_format_success_with_data():
    from formatters import format_success
    out = format_success("ok", {{"key": "val"}})
    assert "[OK]" in out
    assert "key" in out


def test_format_error():
    from formatters import format_error
    out = format_error("something failed", code=2)
    assert "[ERROR]" in out
    assert "code=2" in out


def test_format_table_empty():
    from formatters import format_table
    out = format_table([])
    assert "no data" in out


def test_format_table_rows():
    from formatters import format_table
    rows = [{{"a": "x", "b": "y"}}, {{"a": "p", "b": "q"}}]
    out = format_table(rows)
    assert "a" in out
    assert "x" in out


def test_cmd_{c0}_importable():
    from commands import cmd_{c0}
    assert callable(cmd_{c0})


def test_cmd_{c0}_runs():
    from commands import cmd_{c0}
    out = cmd_{c0}([])
    assert "[OK]" in out
    assert "{c0}" in out


def test_cmd_{c0}_verbose():
    from commands import cmd_{c0}
    out = cmd_{c0}(["-v", "--target", "svc"])
    assert "svc" in out


def test_cmd_{c1}_runs():
    from commands import cmd_{c1}
    out = cmd_{c1}([])
    assert "[OK]" in out


def test_cmd_{c2}_dry_run():
    from commands import cmd_{c2}
    out = cmd_{c2}(["-n"])
    assert "DRY RUN" in out


def test_cmd_{c2}_real():
    from commands import cmd_{c2}
    out = cmd_{c2}([])
    assert "complete" in out


def test_cmd_{c3}_runs():
    from commands import cmd_{c3}
    out = cmd_{c3}([])
    assert "[OK]" in out


def test_commands_use_parsers():
    """commands module must import from parsers, not redefine parse functions."""
    import commands
    import parsers
    # Both modules must be importable without conflict
    assert hasattr(parsers, "parse_{c0}_args")
    assert hasattr(commands, "cmd_{c0}")


def test_commands_use_formatters():
    """commands module must import from formatters."""
    import commands
    import formatters
    assert hasattr(formatters, "format_success")
    result = commands.cmd_{c0}([])
    # Output must be formatted by format_success (starts with [OK])
    assert result.startswith("[OK]")


def test_no_circular_imports():
    import parsers
    import formatters
    import commands
    assert True
'''

    def _cli_spec(self, app_name: str, commands: list) -> str:
        c0, c1, c2, c3 = commands
        return f"""# S3: Refactor Extract — {app_name}

## Goal

Split the monolithic `main.py` into three modules with clear responsibilities,
preserving all public APIs so that `tests/test_main.py` continues to pass.

## Target Architecture

```
{app_name}/
├── main.py         ← DELETE or reduce to thin entry-point shim
├── parsers.py      ← Argument parsers only (no command logic)
├── formatters.py   ← Output formatters only (no command logic)
├── commands.py     ← Command implementations; imports from parsers and formatters
└── tests/
    └── test_main.py  ← Unchanged
```

## Module Contracts

### `parsers.py`
- **Exports**: `parse_{c0}_args`, `parse_{c1}_args`, `parse_{c2}_args`, `parse_{c3}_args`
- **No imports** from `commands` or `formatters` (standalone)
- Each parser takes `argv: List[str]` and returns `Dict[str, Any]`

### `formatters.py`
- **Exports**: `format_success`, `format_error`, `format_table`
- **No imports** from `commands` or `parsers` (standalone)
- Function signatures preserved exactly

### `commands.py`
- **Exports**: `cmd_{c0}`, `cmd_{c1}`, `cmd_{c2}`, `cmd_{c3}`
- **Imports** `parse_*_args` from `parsers`
- **Imports** `format_success`, `format_error`, `format_table` from `formatters`
- **No imports** from `commands` in `parsers` or `formatters` (no circular deps)

## Import Dependency Rules

```
parsers     ←  commands  →  formatters
(parsers and formatters never import from commands)
```

## Hard Requirements

1. `tests/test_main.py` must pass with `python -m pytest tests/ -q`.
2. Each of `parsers.py`, `formatters.py`, `commands.py` must be independently importable.
3. No circular imports allowed.
4. All public function signatures preserved exactly.
5. Total line count across new modules within ±20% of original `main.py`.
6. `main.py` may be deleted or reduced to a shim.

## Deliverables

- `parsers.py`, `formatters.py`, `commands.py` in workspace root.
- All tests passing.
"""

    def _cli_brief(self, app_name: str) -> str:
        return f"""# S3: Refactor Extract (Brief)

The `main.py` file in `{app_name}` has grown too large and mixes concerns.

Refactor it for better maintainability. The Planner has the target architecture
and module boundary details.

Existing tests in `tests/test_main.py` must continue to pass after the refactor.
"""
