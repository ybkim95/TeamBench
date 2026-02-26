"""
New feature tests — these must pass after implementation.
Do not modify this file.
"""
import pytest
from textparser import TextParser
from new_feature import enable_strict_mode


class TestNewFeatureBasic:
    """Basic smoke tests for strict_mode."""

    def test_function_exists(self):
        """The enable_strict_mode function must be importable."""
        assert callable(enable_strict_mode)

    def test_returns_instance(self):
        """Must return the enhanced instance."""
        obj = TextParser()
        result = enable_strict_mode(obj)
        assert result is obj, "enable_strict_mode must return the same instance"

    def test_instance_still_processes(self):
        """After enhancement, process() must still work."""
        obj = TextParser()
        enable_strict_mode(obj)
        result = obj.process("hello")
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    def test_enhancement_attribute_added(self):
        """A marker attribute should be added to the instance."""
        obj = TextParser()
        enable_strict_mode(obj)
        # At least one new attribute or method should be added
        enhanced_attrs = set(dir(obj)) - set(dir(TextParser()))
        assert len(enhanced_attrs) > 0, (
            "Enhancement must add at least one new attribute or method"
        )


class TestNewFeatureDoesNotBreakLegacy:
    """Enhancement must not break any existing v1 behavior."""

    def setup_method(self):
        self.obj = TextParser()
        enable_strict_mode(self.obj)

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
        assert cfg == {}

    def test_none_input_still_raises(self):
        with pytest.raises(ValueError):
            self.obj.process(None)


class TestNewFeatureMultipleInstances:
    """Enhancement must be instance-scoped, not global."""

    def test_independent_instances(self):
        obj1 = TextParser()
        obj2 = TextParser()
        enable_strict_mode(obj1)
        # obj2 must still work without enhancement
        result = obj2.process("hello")
        assert result["status"] == "ok"

    def test_both_can_be_enhanced(self):
        obj1 = TextParser()
        obj2 = TextParser()
        enable_strict_mode(obj1)
        enable_strict_mode(obj2)
        assert obj1.process("a")["status"] == "ok"
        assert obj2.process("b")["status"] == "ok"

    def test_double_enhancement_is_idempotent(self):
        obj = TextParser()
        r1 = enable_strict_mode(obj)
        r2 = enable_strict_mode(obj)
        assert r1 is obj
        assert r2 is obj
        result = obj.process("test")
        assert result["status"] == "ok"
