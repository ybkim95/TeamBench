# GH1044_plotly.py_5193: Fix issue breaking `fig.write_image()` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/5187
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Hi, it seems that setting the `ENABLE_KALEIDO_V0_DEPRECATION_WARNINGS = False` broke the `write_image()` method.

https://github.com/plotly/plotly.py/blob/1462f3f403006edb4044493a96b405e9a9ed0c0a/plotly/basedatatypes.py#L3898-L3912

(withheld: the upstream fix is not part of the task)files#diff-e30d1d28e90c51821f0eeed0db68656f4317c0754deaec93c3365b8a93b4caefR14

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I see this problem too (it broke CI tests). I am not familiar with the source code but superficially, it works if one removes one level of indentation for `return pio.write_image(self, *args, **kwargs)`.

### Comment 2 ([user]):

regression test

```python
import plotly.graph_objects as go
import numpy as np

def test_write_image(tmp_path):

    np.random.seed(1)

    N = 100
    x = np.random.rand(N)
    y = np.random.rand(N)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="markers",
    ))

    fig.write_image(tmp_path / "fig1.png")

    assert (tmp_path /"fig1.png").exists()
```

```
E       AssertionError: assert False
E        +  where False = exists()
E        +    where exists = (PosixPath('/tmp/pytest-of-remi-gau/pytest-9/test_write_image0') / 'fig1.png').exists
```

Version tested

|plotly | kaleido  | test |
|-      |-         |-     |
|6.0.1  |0.2.1     | ✅   |
|6.1.0  |0.2.1     | ❌   |
|6.1.0  |1.0.0rc13 | ❌   |

Also note that kaleido extra dependency

https://github.com/plotly/plotly.py/blob/1462f3f403006edb4044493a96b405e9a9ed0c0a/pyproject.toml#L49

will only work if the use ask for `--prerelease`.

Without this, pip install effectively falls back to 6.0.1.

```bash
$ pip install 'plotly[kaleido]' 

Resolved 3 packages in 6ms
Installed 3 packages in 291ms
 + narwhals==1.39.1
 + packaging==25.0
 + plotly==6.0.1
warning: The package `plotly==6.0.1` does not have an extra named `kaleido`
```

```
$ pip install --prerelease 'plotly[kaleido]'

Resolved 8 packages in 10ms
Installed 6 packages in 189ms
 + choreographer==1.0.7
 + kaleido==1.0.0rc13
 + logistro==1.1.0
 + orjson==3.10.18
 + plotly==6.1.0
 + simplejson==3.20.1
```

### Comment 3 ([user]):

Same issue. When I call write_image with plotly 6.1.0 it silently fails to write an image (no error is raised). Reverting to plotly 6.0.1 resolves the issue. 

I strongly suggest pulling 6.1.0 from PyPi because of the fact that this happens silently.

### Comment 4 ([user]):

cc [user] [user]

### Comment 5 ([user]):

[user] [user] This issue has been fixed and released in [Plotly.py 6.1.1](https://github.com/plotly/plotly.py/releases/tag/v6.1.1). Thank you for reporting.

### Comment 6 ([user]):

Thanks a lot!

### Comment 7 ([user]):

Thank you, great work!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
