"""
Parameterized generator for S4: Backward Compatibility Trap.

TNI Pattern A,C:
  - Spec lists the new feature requirements AND backward-compat constraints
    (existing API signatures must not change, old config format must still work,
    deprecated functions must still be callable, output format for v1 clients
    must be preserved).
  - Brief says "Add the requested feature to the application." without
    mentioning any backward-compat requirements.

Each seed produces:
  - Different library type (parser, formatter, calculator, validator)
  - Different feature type (e.g. strict_mode, batch processing, caching)
  - Different number/type of compat constraints (3-5)
  - A Python library package with existing API and legacy tests
  - An empty new_feature.py stub the agent must fill
  - grade.sh with 10+ checks (new feature works + all compat preserved)
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Domain pools ─────────────────────────────────────────────────────────────

# (library_type, module_name, class_name, short_desc)
LIBRARY_DOMAINS = [
    ("parser",    "textparser",   "TextParser",    "text parsing"),
    ("formatter", "dataformatter","DataFormatter",  "data formatting"),
    ("calculator","mathcalc",     "MathCalc",       "mathematical calculation"),
    ("validator", "schemaval",    "SchemaValidator","schema validation"),
    ("converter", "typeconv",     "TypeConverter",  "type conversion"),
    ("serializer","objserial",    "ObjSerializer",  "object serialization"),
    ("analyzer",  "codeanalyzer", "CodeAnalyzer",   "code analysis"),
    ("encoder",   "dataencoder",  "DataEncoder",    "data encoding"),
]

# (feature_name, feature_func, feature_desc)
NEW_FEATURES = [
    ("strict_mode",    "enable_strict_mode",   "strict validation that raises on any anomaly"),
    ("batch_process",  "process_batch",        "batch processing of multiple inputs at once"),
    ("caching",        "enable_cache",         "result caching to avoid redundant computation"),
    ("async_support",  "process_async",        "async/await compatible processing interface"),
    ("plugin_hooks",   "register_hook",        "plugin hook registration for pre/post processing"),
    ("streaming",      "process_stream",       "streaming/chunked processing for large inputs"),
    ("metrics",        "get_metrics",          "runtime metrics collection and reporting"),
    ("compression",    "enable_compression",   "transparent compression of outputs"),
]

# Each entry: list of (constraint_id, description, what_to_check)
COMPAT_CONSTRAINT_SETS = [
    [
        ("sig_unchanged",     "Original constructor signature `__init__(self, config=None)` must not change"),
        ("v1_output",         "The `process()` method must still return a plain dict for v1 clients"),
        ("deprecated_ok",     "Deprecated `run()` alias must still be callable and return same result as `process()`"),
        ("config_str_ok",     "Passing `config` as a plain string (legacy format) must still work"),
        ("error_msg_stable",  "ValueError message for invalid input must still start with 'Invalid input:'"),
    ],
    [
        ("sig_unchanged",     "Original constructor signature `__init__(self, config=None)` must not change"),
        ("v1_output",         "The `process()` method must still return a plain dict for v1 clients"),
        ("deprecated_ok",     "Deprecated `execute()` alias must still be callable and return same result as `process()`"),
        ("none_config_ok",    "Passing `config=None` (legacy default) must still produce the default behavior"),
        ("key_order_stable",  "Dict keys returned by `process()` must include 'result' and 'status' at minimum"),
    ],
    [
        ("sig_unchanged",     "Original constructor signature `__init__(self, config=None)` must not change"),
        ("v1_output",         "The `process()` method must still return a plain dict for v1 clients"),
        ("deprecated_ok",     "Deprecated `transform()` alias must still be callable and return same result as `process()`"),
        ("config_dict_ok",    "Passing `config` as a dict (legacy format) must still work"),
        ("exception_compat",  "RuntimeError (not a new exception type) must be raised on processing failure"),
    ],
    [
        ("sig_unchanged",     "Original constructor signature `__init__(self, config=None)` must not change"),
        ("v1_output",         "The `process()` method must still return a plain dict for v1 clients"),
        ("deprecated_ok",     "Deprecated `apply()` alias must still be callable and return same result as `process()`"),
        ("positional_ok",     "Calling `process(data)` positionally (not as keyword) must still work"),
        ("version_attr",      "`__version__` attribute on the class must remain '1.x' series (not bumped to 2.x)"),
    ],
]

# Deprecated alias names (one per constraint set, matching deprecated_ok above)
DEPRECATED_ALIASES = ["run", "execute", "transform", "apply"]

# Return value field sets per constraint set
RETURN_FIELDS = [
    {"result": "processed value", "status": "ok", "version": "1"},
    {"result": "processed value", "status": "ok", "meta": "{}"},
    {"result": "processed value", "status": "ok", "elapsed": "0"},
    {"result": "processed value", "status": "ok", "checksum": "0"},
]


class Generator(TaskGenerator):
    task_id = "S4_backward_compat"
    domain = "software"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Use modular indexing for pools that must vary across consecutive seeds,
        # so seeds 0,1,2 are guaranteed to pick distinct entries.
        lib_type, module_name, class_name, lib_desc = LIBRARY_DOMAINS[seed % len(LIBRARY_DOMAINS)]
        feat_name, feat_func, feat_desc = NEW_FEATURES[seed % len(NEW_FEATURES)]
        constraint_idx = seed % len(COMPAT_CONSTRAINT_SETS)
        constraints = COMPAT_CONSTRAINT_SETS[constraint_idx]
        deprecated_alias = DEPRECATED_ALIASES[constraint_idx]
        return_fields = RETURN_FIELDS[constraint_idx]
        version_str = f"1.{rng.randint(2, 9)}.{rng.randint(0, 5)}"

        # Extra field key used in return value (varies by seed)
        extra_key = list(return_fields.keys())[2]  # third key beyond result/status
        extra_val_template = return_fields[extra_key]

        workspace_files = {}

        # ── Main library module ───────────────────────────────────────────────
        workspace_files[f"{module_name}/__init__.py"] = self._gen_init(
            module_name, class_name, version_str
        )
        workspace_files[f"{module_name}/core.py"] = self._gen_core(
            class_name, deprecated_alias, extra_key, extra_val_template, version_str
        )
        workspace_files[f"{module_name}/exceptions.py"] = self._gen_exceptions()
        workspace_files[f"{module_name}/utils.py"] = self._gen_utils()

        # ── New feature stub (agent must implement) ───────────────────────────
        workspace_files["new_feature.py"] = self._gen_new_feature_stub(
            module_name, class_name, feat_name, feat_func, feat_desc
        )

        # ── Legacy tests (must keep passing) ─────────────────────────────────
        workspace_files["tests/__init__.py"] = ""
        workspace_files["tests/test_legacy.py"] = self._gen_legacy_tests(
            module_name, class_name, deprecated_alias, extra_key, version_str
        )

        # ── New feature tests (agent must also pass these) ────────────────────
        workspace_files["tests/test_new_feature.py"] = self._gen_new_feature_tests(
            module_name, class_name, feat_name, feat_func, feat_desc
        )

        # ── Config files ──────────────────────────────────────────────────────
        workspace_files["setup.py"] = self._gen_setup(module_name, version_str)
        workspace_files["README.md"] = self._gen_readme(
            module_name, class_name, feat_name, feat_desc, lib_desc
        )

        expected = {
            "lib_type": lib_type,
            "module_name": module_name,
            "class_name": class_name,
            "feat_name": feat_name,
            "feat_func": feat_func,
            "deprecated_alias": deprecated_alias,
            "version_str": version_str,
            "extra_key": extra_key,
            "constraint_ids": [c[0] for c in constraints],
            "num_constraints": len(constraints),
        }

        spec_md = self._gen_spec(
            module_name, class_name, lib_desc,
            feat_name, feat_func, feat_desc,
            deprecated_alias, extra_key, version_str,
            constraints,
        )
        brief_md = self._gen_brief(
            module_name, class_name, feat_name, feat_func, feat_desc
        )

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── File generators ───────────────────────────────────────────────────────

    def _gen_init(self, module_name: str, class_name: str, version: str) -> str:
        return f'''"""
{module_name} - A {module_name.replace("_", " ")} library.
"""
from {module_name}.core import {class_name}

__version__ = "{version}"
__all__ = ["{class_name}"]
'''

    def _gen_core(
        self,
        class_name: str,
        deprecated_alias: str,
        extra_key: str,
        extra_val_template: str,
        version: str,
    ) -> str:
        # extra_val_template is a string literal value hint
        if extra_key == "version":
            extra_val_expr = '"1"'
        elif extra_key == "meta":
            extra_val_expr = '"{}"'
        elif extra_key == "elapsed":
            extra_val_expr = "0"
        elif extra_key == "checksum":
            extra_val_expr = "0"
        else:
            extra_val_expr = '"unknown"'

        return f'''"""
Core implementation of {class_name}.

IMPORTANT: This is a stable v1 library. Backward compatibility is critical.
Do NOT change any existing public method signatures or return value shapes.
"""
import warnings


class {class_name}:
    """
    Main class for the library. v1 stable API.

    Args:
        config: Optional configuration. Accepts None (default), str, or dict.
    """

    __version__ = "{version}"

    def __init__(self, config=None):
        self._config = self._parse_config(config)
        self._initialized = True

    def _parse_config(self, config):
        """Parse config accepting None, str, or dict (all legacy formats)."""
        if config is None:
            return {{}}
        if isinstance(config, str):
            # Legacy string config: "key=value,key2=value2"
            result = {{}}
            for part in config.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = v.strip()
            return result
        if isinstance(config, dict):
            return dict(config)
        raise ValueError("Invalid input: config must be None, str, or dict")

    def process(self, data):
        """
        Process the given data and return a result dict.

        Returns:
            dict with keys: 'result', 'status', '{extra_key}'
        """
        if data is None:
            raise ValueError("Invalid input: data cannot be None")
        if not isinstance(data, (str, int, float, list, dict)):
            raise RuntimeError(f"Unsupported data type: {{type(data).__name__}}")

        processed = self._do_process(data)
        return {{
            "result": processed,
            "status": "ok",
            "{extra_key}": {extra_val_expr},
        }}

    def _do_process(self, data):
        """Internal processing logic."""
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, (int, float)):
            return data
        if isinstance(data, list):
            return [self._do_process(item) for item in data]
        if isinstance(data, dict):
            return {{k: self._do_process(v) for k, v in data.items()}}
        return data

    def {deprecated_alias}(self, data):
        """
        Deprecated alias for process(). Kept for backward compatibility.

        .. deprecated::
            Use process() instead. This alias will be removed in v2.0.
        """
        warnings.warn(
            "{deprecated_alias}() is deprecated, use process() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.process(data)

    def get_config(self):
        """Return current configuration dict."""
        return dict(self._config)

    def reset(self):
        """Reset to default configuration."""
        self._config = {{}}
'''

    def _gen_exceptions(self) -> str:
        return '''"""
Custom exceptions for the library.
These exception types are part of the public API - do not rename or remove.
"""


class LibraryError(Exception):
    """Base exception for library errors."""
    pass


class ConfigError(LibraryError):
    """Raised when configuration is invalid."""
    pass


class ProcessingError(LibraryError):
    """Raised when processing fails unrecoverably."""
    pass
'''

    def _gen_utils(self) -> str:
        return '''"""
Internal utility functions.
These are private and may change between versions.
"""


def normalize_string(s: str) -> str:
    """Normalize whitespace in a string."""
    return " ".join(s.split())


def flatten_dict(d: dict, prefix: str = "") -> dict:
    """Flatten a nested dict to dot-separated keys."""
    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_dict(v, key))
        else:
            result[key] = v
    return result


def safe_cast(value, target_type, default=None):
    """Safely cast a value to target_type, returning default on failure."""
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default
'''

    def _gen_new_feature_stub(
        self,
        module_name: str,
        class_name: str,
        feat_name: str,
        feat_func: str,
        feat_desc: str,
    ) -> str:
        return f'''"""
New feature implementation: {feat_name}

Add {feat_desc} to {class_name} WITHOUT breaking any existing behavior.

Instructions:
  1. Implement the `{feat_func}` function below.
  2. Monkey-patch or subclass {class_name} if needed, but do NOT modify core.py.
  3. All existing tests in tests/test_legacy.py must continue to pass.
  4. The new tests in tests/test_new_feature.py must also pass.
"""
from {module_name} import {class_name}


def {feat_func}(instance):
    """
    Add {feat_desc} capability to an existing {class_name} instance.

    Args:
        instance: An existing {class_name} instance to enhance.

    Returns:
        The enhanced instance (same object, augmented in-place).

    TODO: Implement this function.
    """
    raise NotImplementedError("{feat_func} is not yet implemented")
'''

    def _gen_legacy_tests(
        self,
        module_name: str,
        class_name: str,
        deprecated_alias: str,
        extra_key: str,
        version: str,
    ) -> str:
        major_minor = ".".join(version.split(".")[:2])
        return f'''"""
Legacy tests — these MUST continue to pass after the new feature is added.
Do not modify this file.
"""
import warnings
import pytest
from {module_name} import {class_name}


class TestConstructorBackwardCompat:
    """Constructor must keep working with all legacy call patterns."""

    def test_no_args(self):
        """Default instantiation (config=None) must work."""
        obj = {class_name}()
        assert obj is not None

    def test_none_explicit(self):
        """Explicit config=None must work."""
        obj = {class_name}(config=None)
        assert obj is not None

    def test_string_config(self):
        """String config format must still be accepted."""
        obj = {class_name}(config="key=value,mode=fast")
        cfg = obj.get_config()
        assert cfg.get("key") == "value"
        assert cfg.get("mode") == "fast"

    def test_dict_config(self):
        """Dict config format must still be accepted."""
        obj = {class_name}(config={{"mode": "strict", "timeout": "30"}})
        cfg = obj.get_config()
        assert cfg["mode"] == "strict"

    def test_positional_config(self):
        """Config as positional arg (not keyword) must work."""
        obj = {class_name}({{"x": "1"}})
        assert obj is not None


class TestProcessReturnShape:
    """Return value shape of process() must be stable."""

    def setup_method(self):
        self.obj = {class_name}()

    def test_returns_dict(self):
        result = self.obj.process("hello")
        assert isinstance(result, dict)

    def test_has_result_key(self):
        result = self.obj.process("hello")
        assert "result" in result

    def test_has_status_key(self):
        result = self.obj.process("hello")
        assert "status" in result

    def test_has_extra_key(self):
        result = self.obj.process("hello")
        assert "{extra_key}" in result

    def test_status_is_ok(self):
        result = self.obj.process("hello")
        assert result["status"] == "ok"

    def test_string_passthrough(self):
        result = self.obj.process("  hello  ")
        assert result["result"] == "hello"

    def test_numeric_passthrough(self):
        result = self.obj.process(42)
        assert result["result"] == 42

    def test_list_passthrough(self):
        result = self.obj.process(["a", "b"])
        assert isinstance(result["result"], list)


class TestDeprecatedAlias:
    """Deprecated {deprecated_alias}() must remain callable and return same shape."""

    def setup_method(self):
        self.obj = {class_name}()

    def test_alias_callable(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = self.obj.{deprecated_alias}("test")
        assert result is not None

    def test_alias_returns_dict(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = self.obj.{deprecated_alias}("test")
        assert isinstance(result, dict)

    def test_alias_same_as_process(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            r1 = self.obj.process("data")
            r2 = self.obj.{deprecated_alias}("data")
        assert r1["result"] == r2["result"]
        assert r1["status"] == r2["status"]

    def test_alias_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.obj.{deprecated_alias}("x")
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


class TestErrorBackwardCompat:
    """Error behavior must remain stable."""

    def setup_method(self):
        self.obj = {class_name}()

    def test_none_data_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            self.obj.process(None)
        assert str(exc_info.value).startswith("Invalid input:")

    def test_bad_type_raises_runtime_error(self):
        with pytest.raises(RuntimeError):
            self.obj.process(object())

    def test_bad_config_raises_value_error(self):
        with pytest.raises(ValueError):
            {class_name}(config=12345)


class TestVersionAttribute:
    """Version attribute must remain in v1.x series."""

    def test_class_has_version(self):
        assert hasattr({class_name}, "__version__")

    def test_version_is_string(self):
        assert isinstance({class_name}.__version__, str)

    def test_version_starts_with_1(self):
        ver = {class_name}.__version__
        assert ver.startswith("1."), f"Expected 1.x version, got {{ver}}"

    def test_module_version_matches(self):
        import {module_name}
        assert {module_name}.__version__ == {class_name}.__version__


class TestGetConfig:
    """get_config() must return a copy, not a reference."""

    def test_returns_dict(self):
        obj = {class_name}(config={{"k": "v"}})
        assert isinstance(obj.get_config(), dict)

    def test_returns_copy(self):
        obj = {class_name}(config={{"k": "v"}})
        cfg = obj.get_config()
        cfg["injected"] = "evil"
        assert "injected" not in obj.get_config()
'''

    def _gen_new_feature_tests(
        self,
        module_name: str,
        class_name: str,
        feat_name: str,
        feat_func: str,
        feat_desc: str,
    ) -> str:
        return f'''"""
New feature tests — these must pass after implementation.
Do not modify this file.
"""
import pytest
from {module_name} import {class_name}
from new_feature import {feat_func}


class TestNewFeatureBasic:
    """Basic smoke tests for {feat_name}."""

    def test_function_exists(self):
        """The {feat_func} function must be importable."""
        assert callable({feat_func})

    def test_returns_instance(self):
        """Must return the enhanced instance."""
        obj = {class_name}()
        result = {feat_func}(obj)
        assert result is obj, "{feat_func} must return the same instance"

    def test_instance_still_processes(self):
        """After enhancement, process() must still work."""
        obj = {class_name}()
        {feat_func}(obj)
        result = obj.process("hello")
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    def test_enhancement_attribute_added(self):
        """A marker attribute should be added to the instance."""
        obj = {class_name}()
        {feat_func}(obj)
        # At least one new attribute or method should be added
        enhanced_attrs = set(dir(obj)) - set(dir({class_name}()))
        assert len(enhanced_attrs) > 0, (
            "Enhancement must add at least one new attribute or method"
        )


class TestNewFeatureDoesNotBreakLegacy:
    """Enhancement must not break any existing v1 behavior."""

    def setup_method(self):
        self.obj = {class_name}()
        {feat_func}(self.obj)

    def test_process_still_returns_dict(self):
        result = self.obj.process("test")
        assert isinstance(result, dict)

    def test_process_still_has_result_key(self):
        result = self.obj.process("test")
        assert "result" in result

    def test_process_still_has_status_key(self):
        result = self.obj.process("test")
        assert "status" in result

    def test_process_status_still_ok(self):
        result = self.obj.process("test")
        assert result["status"] == "ok"

    def test_get_config_still_works(self):
        cfg = self.obj.get_config()
        assert isinstance(cfg, dict)

    def test_reset_still_works(self):
        self.obj.reset()
        cfg = self.obj.get_config()
        assert cfg == {{}}

    def test_none_input_still_raises(self):
        with pytest.raises(ValueError):
            self.obj.process(None)


class TestNewFeatureMultipleInstances:
    """Enhancement must be instance-scoped, not global."""

    def test_independent_instances(self):
        obj1 = {class_name}()
        obj2 = {class_name}()
        {feat_func}(obj1)
        # obj2 must still work without enhancement
        result = obj2.process("hello")
        assert result["status"] == "ok"

    def test_both_can_be_enhanced(self):
        obj1 = {class_name}()
        obj2 = {class_name}()
        {feat_func}(obj1)
        {feat_func}(obj2)
        assert obj1.process("a")["status"] == "ok"
        assert obj2.process("b")["status"] == "ok"

    def test_double_enhancement_is_idempotent(self):
        obj = {class_name}()
        r1 = {feat_func}(obj)
        r2 = {feat_func}(obj)
        assert r1 is obj
        assert r2 is obj
        result = obj.process("test")
        assert result["status"] == "ok"
'''

    def _gen_setup(self, module_name: str, version: str) -> str:
        return f'''from setuptools import setup, find_packages

setup(
    name="{module_name}",
    version="{version}",
    packages=find_packages(),
    python_requires=">=3.8",
)
'''

    def _gen_readme(
        self,
        module_name: str,
        class_name: str,
        feat_name: str,
        feat_desc: str,
        lib_desc: str,
    ) -> str:
        return f'''# {module_name}

A stable v1 {lib_desc} library.

## Usage

```python
from {module_name} import {class_name}

obj = {class_name}()
result = obj.process("hello world")
print(result)  # {{"result": "hello world", "status": "ok", ...}}
```

## Adding the New Feature

The `new_feature.py` file contains a stub for `{feat_name}` ({feat_desc}).
Implement it without breaking any existing behavior.

```python
from new_feature import {feat_name.replace("_", "_")}
```

## Backward Compatibility

This library maintains strict backward compatibility for all v1.x releases.
- `process()` return shape is stable
- Constructor accepts None, str, or dict config
- Deprecated aliases remain callable
- `__version__` stays in 1.x series
'''

    def _gen_spec(
        self,
        module_name: str,
        class_name: str,
        lib_desc: str,
        feat_name: str,
        feat_func: str,
        feat_desc: str,
        deprecated_alias: str,
        extra_key: str,
        version: str,
        constraints: list,
    ) -> str:
        constraint_list = "\n".join(
            f"   {i+1}. **{cid}**: {desc}"
            for i, (cid, desc) in enumerate(constraints)
        )
        return f'''# S4: Backward Compatibility Trap

## Goal

Add the `{feat_name}` feature to the `{module_name}` library while preserving
**all** existing v1 backward-compatibility guarantees.

## Library Overview

`{module_name}` is a stable v1 {lib_desc} library currently at version `{version}`.
Its public API is:

- `{class_name}(config=None)` — constructor, accepts `None`, `str`, or `dict`
- `.process(data)` — processes data, returns a plain `dict` with keys `result`, `status`, `{extra_key}`
- `.{deprecated_alias}(data)` — deprecated alias for `.process()` (emits `DeprecationWarning`)
- `.get_config()` — returns a copy of current config dict
- `.reset()` — resets config to defaults
- `{class_name}.__version__` — version string, currently `{version}`

## New Feature Requirements

Implement `{feat_func}(instance)` in `new_feature.py`:

1. The function accepts an existing `{class_name}` instance.
2. It enhances the instance in-place with {feat_desc} capability.
3. It returns the same instance (not a new object).
4. At least one new attribute or method must be added to the instance.
5. Calling `{feat_func}()` twice on the same instance must be idempotent.
6. The enhancement must be instance-scoped (not affect other instances).

## Backward-Compatibility Constraints

The following constraints MUST be satisfied after your changes. Violating any
one of them constitutes a breaking change and will fail the grade.

{constraint_list}

## Deliverables

1. `new_feature.py` with `{feat_func}` fully implemented (no `NotImplementedError`).
2. All tests in `tests/test_legacy.py` must pass (zero modifications to that file).
3. All tests in `tests/test_new_feature.py` must pass.
4. `{module_name}/core.py` must NOT be modified (API signature preservation).

## Grading

The grader runs:
```
python -m pytest tests/ -q
```
and independently checks each backward-compatibility constraint.
All 10+ checks must pass for full credit.
'''

    def _gen_brief(
        self,
        module_name: str,
        class_name: str,
        feat_name: str,
        feat_func: str,
        feat_desc: str,
    ) -> str:
        return f'''# S4: Backward Compatibility (Brief)

Add the requested feature to the `{module_name}` library.

The feature stub is in `new_feature.py` — implement `{feat_func}()` to add
{feat_desc} to an existing `{class_name}` instance.

The Planner has the full specification including all constraints.
Make sure all tests pass after your implementation.
'''
