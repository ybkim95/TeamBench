# GH915_plotly.py_4926: patch: deepcopy figure fix — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/4925
- Repo: https://github.com/plotly/plotly.py

## Issue Description

The example below throws an error in 6.0.0rc0 but not in 5.24.1

```
    raise ValueError(
ValueError: 
    Invalid value of type 'builtins.dict' received for the 'x' property of scatter
        Received value: {'dtype': 'i2', 'bdata': 'oAelB6oHrwe0B7kHvgfDB8gHzQfSB9cH'}

    The 'x' property is an array that may be specified as a tuple,
    list, numpy array, or pandas Series
```

```
from dash import Dash, dcc, html
import plotly.express as px

import copy

app = Dash(__name__)

gapminder = px.data.gapminder().query("(country=='Canada') | (country=='United States') | (country=='Mexico')")

fig = px.line(gapminder, x="year", y="gdpPercap", color='country')
fig.update_yaxes(title_text='Year')
fig.update_xaxes(title_text='Adoption Rate')

# Default dimensions
fig.update_layout(
    margin=dict(l=60, r=0, t=0, b=60),
)

fig_custom_height = copy.deepcopy(fig)
fig_custom_height.update_layout(height=800)

fig_custom_short_height = copy.deepcopy(fig)
fig_custom_short_height.update_layout(height=200)

app.layout = [
                dcc.Graph(
                figure = fig_custom_height,
                ),
                dcc.Graph(
                figure = fig_custom_short_height,
            ),

]

if __name__ == '__main__':
    app.run_server(debug=True)

```

pip list output:

```
Package              Version
-------------------- -----------
blinker              1.9.0
certifi              2024.8.30
charset-normalizer   3.4.0
click                8.1.7
dash                 2.18.2
dash-core-components 2.0.0
dash-html-components 2.0.0
dash-table           5.0.0
Flask                3.0.3
idna                 3.10
importlib_metadata   8.5.0
itsdangerous         2.2.0
Jinja2               3.1.4
MarkupSafe           3.0.2
narwhals             1.15.2
nest-asyncio         1.6.0
numpy                2.1.3
packaging            24.2
pandas               2.2.3
pip                  23.2.1
plotly               6.0.0rc0
python-dateutil      2.9.0.post0
pytz                 2024.2
requests             2.32.3
retrying             1.3.4
setuptools           65.5.0
six                  1.16.0
tenacity             9.0.0
typing_extensions    4.12.2
tzdata               2024.2
urllib3              2.2.3
Werkzeug             3.0.6
zipp                 3.21.0
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I was able to bisect it to the following commit: (withheld: the upstream fix is not part of the task)
Specifically `is_typed_array_spec` was the only function checking for dict type.

### Comment 2 ([user]):

[user] Thank you for finding that! I think we can put those changes back in. I was not expecting the typed arrays to be input to validators anymore but I see that this is a case where they might be showing up for validation. If we bypass validation when we encounter typed array spec it should work, so maybe I'll just revert those changes.

### Comment 3 ([user]):

I am running tests reverting those changes! I can open a PR if everything goes smooth :)

Edit: I wonder if there are specific tests worth adding

### Comment 4 ([user]):

[user] [user] what's the status on this one now? thanks - [user]

### Comment 5 ([user]):

I approved the PR to fix this! [user] should I go ahead and merge?

### Comment 6 ([user]):

please!

## PR Review Comments

**[user]** on `packages/python/plotly/_plotly_utils/basevalidators.py`:

🤔 different black version?

**[user]** on `packages/python/plotly/_plotly_utils/basevalidators.py`:

Oh interesting! Yeah not sure why that's happening but it looks fine?

**[user]** on `packages/python/plotly/_plotly_utils/tests/validators/test_fig_deepcopy.py`:

This test looks good thank you for doing that! Do you think you could add a simple check that the data did copy correctly? Also, where are the other deepcopy tests you mentioned? Does it make more sense to include this test with those?

**[user]** on `packages/python/plotly/_plotly_utils/tests/validators/test_fig_deepcopy.py`:

Thanks [user] , what's the best way to assert that the values are the same? is it `fig_copy.to_dict() == fig.to_dict()`?

Here are few other figure deepcopy's in the test suite:
- [test_update_subplots](https://github.com/plotly/plotly.py/blob/725290068d5ea3f7f344eec7d7b84c58b85cfb38/packages/python/plotly/plotly/tests/test_core/test_update_objects/test_update_subplots.py#L364)
- [test_update_traces](https://github.com/plotly/plotly.py/blob/725290068d5ea3f7f344eec7d7b84c58b85cfb38/packages/python/plotly/plotly/tests/test_core/test_update_objects/test_update_traces.py#L295)
- [test_deepcopy_pickle.py](https://github.com/plotly/plotly.py/blob/725290068d5ea3f7f344eec7d7b84c58b85cfb38/packages/python/plotly/plotly/tests/test_io/test_deepcopy_pickle.py#L38)

**[user]** on `packages/python/plotly/_plotly_utils/basevalidators.py`:

Yeah I would not worry too much about this, I just wonder why that's the case 😇

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
