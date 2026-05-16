# GH7: Fix Fixture State Isolation Between Test Modules

The test framework has a bug where session-scoped fixtures leak mutable
state between test modules. Tests that pass in isolation fail when run
together because fixture state accumulates across modules.

Fix the fixture manager in `test_framework.py`.
