"""
Legacy tests — these MUST continue to pass after the new feature is added.
Do not modify this file.
"""
import warnings
import pytest
from textparser import TextParser


class TestConstructorBackwardCompat:
    """Constructor must keep working with all legacy call patterns."""

    def test_no_args(self):
        """Default instantiation (config=None) must work."""
        obj = TextParser()
        assert obj is not None

    def test_none_explicit(self):
        """Explicit config=None must work."""
        obj = TextParser(config=None)
        assert obj is not None

    def test_string_config(self):
        """String config format must still be accepted."""
        obj = TextParser(config="key=value,mode=fast")
        cfg = obj.get_config()
        assert cfg.get("key") == "value"
        assert cfg.get("mode") == "fast"

    def test_dict_config(self):
        """Dict config format must still be accepted."""
        obj = TextParser(config={"mode": "strict", "timeout": "30"})
        cfg = obj.get_config()
        assert cfg["mode"] == "strict"

    def test_positional_config(self):
        """Config as positional arg (not keyword) must work."""
        obj = TextParser({"x": "1"})
        assert obj is not None


class TestProcessReturnShape:
    """Return value shape of process() must be stable."""

    def setup_method(self):
        self.obj = TextParser()

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
        assert "version" in result

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
    """Deprecated run() must remain callable and return same shape."""

    def setup_method(self):
        self.obj = TextParser()

    def test_alias_callable(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = self.obj.run("test")
        assert result is not None

    def test_alias_returns_dict(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = self.obj.run("test")
        assert isinstance(result, dict)

    def test_alias_same_as_process(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            r1 = self.obj.process("data")
            r2 = self.obj.run("data")
        assert r1["result"] == r2["result"]
        assert r1["status"] == r2["status"]

    def test_alias_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.obj.run("x")
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


class TestErrorBackwardCompat:
    """Error behavior must remain stable."""

    def setup_method(self):
        self.obj = TextParser()

    def test_none_data_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            self.obj.process(None)
        assert str(exc_info.value).startswith("Invalid input:")

    def test_bad_type_raises_runtime_error(self):
        with pytest.raises(RuntimeError):
            self.obj.process(object())

    def test_bad_config_raises_value_error(self):
        with pytest.raises(ValueError):
            TextParser(config=12345)


class TestVersionAttribute:
    """Version attribute must remain in v1.x series."""

    def test_class_has_version(self):
        assert hasattr(TextParser, "__version__")

    def test_version_is_string(self):
        assert isinstance(TextParser.__version__, str)

    def test_version_starts_with_1(self):
        ver = TextParser.__version__
        assert ver.startswith("1."), f"Expected 1.x version, got {ver}"

    def test_module_version_matches(self):
        import textparser
        assert textparser.__version__ == TextParser.__version__


class TestGetConfig:
    """get_config() must return a copy, not a reference."""

    def test_returns_dict(self):
        obj = TextParser(config={"k": "v"})
        assert isinstance(obj.get_config(), dict)

    def test_returns_copy(self):
        obj = TextParser(config={"k": "v"})
        cfg = obj.get_config()
        cfg["injected"] = "evil"
        assert "injected" not in obj.get_config()
