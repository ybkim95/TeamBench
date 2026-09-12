# GH898_plotly.py_5322: Fix broken import in `mplexporter` tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/5253
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Since the 6.2.0 release, `pytest` fails to collect matplot tests:

```pytb
========================================================= test session starts =========================================================
platform linux -- Python 3.13.5, pytest-8.4.1, pluggy-1.6.0
rootdir: /tmp/plotly.py
configfile: pyproject.toml
plugins: anyio-4.9.0, typeguard-4.4.4
collected 3383 items / 1 error                                                                                                        

=============================================================== ERRORS ================================================================
________________________________ ERROR collecting plotly/matplotlylib/mplexporter/tests/test_utils.py _________________________________
ImportError while importing test module '/tmp/plotly.py/plotly/matplotlylib/mplexporter/tests/test_utils.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
plotly/matplotlylib/mplexporter/tests/test_utils.py:2: in <module>
    from . import plt
E   ImportError: cannot import name 'plt' from 'plotly.matplotlylib.mplexporter.tests' (/tmp/plotly.py/plotly/matplotlylib/mplexporter/tests/__init__.py)
========================================================== warnings summary ===========================================================
plotly/conftest.py:4
  /tmp/plotly.py/plotly/conftest.py:4: PytestRemovedIn9Warning:
  
  The (path: py.path.local) argument is deprecated, please use (collection_path: pathlib.Path)
  see https://docs.pytest.org/en/latest/deprecations.html#py-path-local-arguments-for-hooks-replaced-with-pathlib-path

tests/test_io/test_to_from_plotly_json.py:112
  /tmp/plotly.py/tests/test_io/test_to_from_plotly_json.py:112: UserWarning:
  
  no explicit representation of timezones available for np.datetime64

.venv/lib/python3.13/site-packages/pdfrw/objects/pdfstring.py:120
  /tmp/plotly.py/.venv/lib/python3.13/site-packages/pdfrw/objects/pdfstring.py:120: SyntaxWarning:
  
  invalid escape sequence '\('

.venv/lib/python3.13/site-packages/pdfrw/objects/pdfstring.py:375
  /tmp/plotly.py/.venv/lib/python3.13/site-packages/pdfrw/objects/pdfstring.py:375: SyntaxWarning:
  
  invalid escape sequence '\['

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================= short test summary info =======================================================
ERROR plotly/matplotlylib/mplexporter/tests/test_utils.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
==================================================== 4 warnings, 1 error in 8.27s =====================================================
```

This seems to be caused by eb95abc4d52a9c3ed231c5509ee9cc12804d1107 that removed the `plt` import from `plotly/matplotlylib/mplexporter/tests/__init__.py`.

To reproduce:

```
pip install -e .[dev_optional] matplotlib
pytest
```

CC [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Sorry, meant 6.2.0.

### Comment 2 ([user]):

i also started getting broken internal imports

```py
---> 16 from plotly.validators.scatter.line import DashValidator
     17 from plotly.validators.scatter.marker import SymbolValidator
     18 from tqdm import tqdm

ModuleNotFoundError: No module named 'plotly.validators.scatter'
```

downgrading to `plotly==6.1.1` fixes the issue

### Comment 3 ([user]):

thanks for the report and confirmation - I'll try to prioritize work on this problem this week.

### Comment 4 ([user]):

from my side this issue is resolved thanks to (withheld: the upstream fix is not part of the task). no need to restore `SymbolValidator` or `DashValidator` but i recommend the [v6.2.0 release notes](https://github.com/plotly/plotly.py/releases/tag/v6.2.0) be updated to document this breaking change!

### Comment 5 ([user]):

The test suite is still broken in 6.3.0, though.

### Comment 6 ([user]):

Filed #5322 to fix this.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
