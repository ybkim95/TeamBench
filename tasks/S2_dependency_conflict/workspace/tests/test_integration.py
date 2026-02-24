import json


def test_libfoo_import():
    from libfoo_core import foo_process
    result = foo_process("hello")
    assert result["mode"] == "foo"


def test_libbar_import():
    from libbar_core import bar_process
    result = bar_process("world")
    assert result["mode"] == "bar"


def test_utils_version():
    import utils
    assert hasattr(utils, '__version__'), "utils missing __version__"


def test_both_together():
    from libfoo_core import foo_process
    from libbar_core import bar_process
    r1 = foo_process("x")
    r2 = bar_process("y")
    assert r1["version"] == r2["version"], "version mismatch between libs"
