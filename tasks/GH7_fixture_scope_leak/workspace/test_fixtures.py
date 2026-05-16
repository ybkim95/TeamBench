from test_framework import FixtureManager, TestRunner, Fixture


def test_function_scope_isolation():
    """Function-scoped fixtures are fresh per test."""
    mgr = FixtureManager()
    mgr.register("items", lambda: [], scope="function")

    val1 = mgr.get_fixture("items", scope_key="test_a")
    val1.append("from_test_a")

    # Clear function scope between tests
    mgr.clear_scope("function")

    val2 = mgr.get_fixture("items", scope_key="test_b")
    assert val2 == [], f"Function scope leaked: {val2}"


def test_session_scope_leak():
    """THE BUG: Session-scoped mutable fixture leaks between modules."""
    mgr = FixtureManager()
    mgr.register("registry", lambda: [], scope="session")

    # Module A uses the fixture
    val_a = mgr.get_fixture("registry", scope_key="module_a")
    val_a.append("item_from_a")

    # Module B gets "fresh" fixture — but it's the same object!
    val_b = mgr.get_fixture("registry", scope_key="module_b")
    assert val_b == [], f"Session scope leaked: {val_b}"


def test_session_scope_dict_leak():
    """Dict fixtures also leak."""
    mgr = FixtureManager()
    mgr.register("config", lambda: {"debug": False}, scope="session")

    val_a = mgr.get_fixture("config", scope_key="module_a")
    val_a["debug"] = True
    val_a["extra_key"] = "leaked"

    val_b = mgr.get_fixture("config", scope_key="module_b")
    assert val_b == {"debug": False}, f"Dict leaked: {val_b}"


def test_session_immutable_cached():
    """Immutable session fixtures should still be cached (no waste)."""
    call_count = 0

    def make_config():
        nonlocal call_count
        call_count += 1
        return "immutable_string"

    mgr = FixtureManager()
    mgr.register("name", make_config, scope="session")

    val1 = mgr.get_fixture("name", scope_key="mod_a")
    val2 = mgr.get_fixture("name", scope_key="mod_b")
    assert val1 == val2 == "immutable_string"
    # Factory should only be called once (cached)
    assert call_count == 1


def test_runner_integration():
    """Full integration: two modules with session fixture."""
    mgr = FixtureManager()
    mgr.register("shared_list", lambda: ["initial"], scope="session")

    # Module 1: modifies the fixture
    def mod1_test(shared_list):
        shared_list.append("mod1_added")
        assert len(shared_list) == 2  # initial + mod1_added

    # Module 2: should get clean fixture
    def mod2_test(shared_list):
        assert len(shared_list) == 1, f"Expected 1 item, got {len(shared_list)}: {shared_list}"
        assert shared_list == ["initial"]

    runner = TestRunner(mgr)
    r1 = runner.run_module("module1", {"test_mod1": mod1_test}, ["shared_list"])
    r2 = runner.run_module("module2", {"test_mod2": mod2_test}, ["shared_list"])

    assert r1[0][1] == True, f"Module 1 test failed: {r1[0][2]}"
    assert r2[0][1] == True, f"Module 2 test failed: {r2[0][2]}"


def test_module_scope_works():
    """Module-scoped fixtures cleared between modules (already correct)."""
    mgr = FixtureManager()
    mgr.register("mod_items", lambda: [], scope="module")

    val_a = mgr.get_fixture("mod_items", scope_key="mod_a")
    val_a.append("item")

    mgr.clear_scope("module")

    val_b = mgr.get_fixture("mod_items", scope_key="mod_b")
    assert val_b == [], f"Module scope should be cleared: {val_b}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print(f"  PASS: {name}")
            except (AssertionError, Exception) as e:
                print(f"  FAIL: {name}: {e}")
