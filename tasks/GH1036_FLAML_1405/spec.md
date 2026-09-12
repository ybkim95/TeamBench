# GH1036_FLAML_1405: fix: Fixed bug where group folds and sample weights couldn't be used together — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1396
- Repo: https://github.com/microsoft/FLAML

## Issue Description

### Describe the bug

Hi,

I've found an issue where group folds cannot be used with sample weights, under certain circumstances. There are (I believe) three requirements for this error to occur.

- We set `split_type='group'`.
- `sample_weights` is a Pandas Series
- The indices of the sample_weights aren't equal to `range(len(y_train.shape[0]))` i.e. some indices may be out of order/missing.

When these criteria are met, we receive a KeyError, such as the one shown below:

![Image](https://github.com/user-attachments/assets/4ac5bbc0-302e-4dbd-a250-ddea6bb9583b)

It's worth emphasising that if we don't use `GroupKFolds` (i.e. we set split_type='uniform'), then this issue doesn't occur - everything works well.

### Steps to reproduce

Example code which generates this error is shown below. Essentially we use the Iris dataset as a regression dataset, and append a cluster column to the dataset, and generate some toy sample weights. We then split the data, groups and sample weights into train and test sets. Here we are using FLAML to perform the train and validation steps, whilst we withhold the test set to measure performance against afterwards.

```
from sklearn import datasets
import numpy as np
from flaml import AutoML
from sklearn.model_selection import train_test_split
import pandas as pd
iris_dict_data = datasets.load_iris(as_frame=True)  # numpy arrays
iris_data = iris_dict_data["frame"]  # pandas dataframe data + target
iris_data['cluster'] = np.random.randint(0, 5, iris_data.shape[0])
automl = AutoML()

X= iris_data[["sepal length (cm)","sepal width (cm)", "petal length (cm)"]].to_numpy()
y = iris_data["petal width (cm)"]
sample_weight = pd.Series(np.random.rand(X.shape[0]))
X_train, X_test, y_train, y_test, groups_train, groups_test, sample_weight_train, sample_weight_test = train_test_split(X, y, iris_data['cluster'], sample_weight, random_state=42)
automl_settings = {
    "max_iter":5,
    "time_budget":-1,
    "metric": 'r2',
    "task": 'regression',
    "log_file_name": "error.log",
    "log_type": "all",
    "estimator_list": ['lgbm'],
    "eval_method": "cv",
    "split_type":"group",
    "groups":groups_train,
    "sample_weight": sample_weight_train
}

automl.fit(X_train, y_train, **automl_settings)
```

I believe I've found the cause of this issue. Essentially if `split_type` is in `SHUFFLE_SPLIT_TYPES ` ('uniform' or 'stratified') then the index of `sample_weight_all` is reset (this is on `general_task.py`)

```
        elif split_type in SHUFFLE_SPLIT_TYPES:
                ...
                if isinstance(state.sample_weight_all, pd.Series):
                    state.sample_weight_all.reset_index(drop=True, inplace=True)
```

The error originates on line 773 of `generic_task.py`, that is, this line:
```
                    fit_kwargs["sample_weight"], weight_val = (
                        weight[train_index],
                        weight[val_index],
                    )
```
The indices don't align, so we get a `KeyError`. I can see a couple of possible fixes for this:

1. Reset the indices of the sample weights 
2. Extract the weights the same way the groups are extracted on line 776 of`generic_task.py`, which is as follows:
```
                if groups is not None:
                    fit_kwargs["groups"] = (
                        groups[train_index] if isinstance(groups, np.ndarray) else groups.iloc[train_index]
                    )
                    groups_val = groups[val_index] if isinstance(groups, np.ndarray) else groups.iloc[val_index]
```
If we update the erroneous code on line 773 as follows:

```
                    fit_kwargs["sample_weight"] = (
                        weight[train_index] if isinstance(weight, np.ndarray) else weight.iloc[train_index]
                    )
                    weight_val = weight[val_index] if isinstance(weight, np.ndarray) else weight.iloc[val_index]
```

then it fixes the issue.

Please let me know if you have any strong opinions on this! Personally I like the latter solution.

### Additional Information

Python 3.10.13
FLAML Version 2.3.3

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] , thank you for reporting this. This is similar to #1384 which you've fixed in #1385 . Please go ahead to raise a PR for this one as well. I prefer your second proposal.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
