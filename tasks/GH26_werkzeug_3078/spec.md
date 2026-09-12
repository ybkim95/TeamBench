# GH26_werkzeug_3078: initialize `_pin` in debugger — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3075
- Repo: https://github.com/pallets/werkzeug

## Issue Description

Starting with werkzeug 3.1.4, passing `pin_security=False` to `DebugApplication()` raises an exception:

```
from django.core.wsgi import get_wsgi_application

from werkzeug.debug import DebuggedApplication

application = DebuggedApplication(get_wsgi_application(), evalex=True, pin_security=False)
```

```
  File "/home/<redacted>/code/<redacted>/wsgi.py", line 6, in <module>
    application = DebuggedApplication(get_wsgi_application(), evalex=True, pin_security=False)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/<redacted>/.virtualenvs/<redacted>/lib/python3.12/site-packages/werkzeug/debug/__init__.py", line 303, in _
_init__
    self.pin = None
    ^^^^^^^^
  File "/home/<redacted>/.virtualenvs/<redacted>/lib/python3.12/site-packages/werkzeug/debug/__init__.py", line 323, in p
in
    del self._pin
        ^^^^^^^^^
AttributeError: 'DebuggedApplication' object has no attribute '_pin'
```

<!--
Describe the expected behavior that should have happened but didn't.
-->

Environment:

- Python version:  3.12
- Werkzeug version:  3.1.4

Appears to have been introduced by (withheld: the upstream fix is not part of the task)#diff-83867b1c4c9b75c728654ed284dc98f7c8d4e8bd682fc31b977d122dd045178a

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
