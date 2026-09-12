# GH1188_FLAML_1500: Add validation and clear error messages for custom_metric parameter — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

## Plan: Add validation and better error handling for custom_metric parameter

The issue occurs when users incorrectly call the custom_metric function instead of passing it as a reference. The current code doesn't validate that the metric parameter is callable when it's not a string, leading to confusing errors.

### Changes completed:
- [x] Explore the codebase to understand the issue
- [x] Add validation in `AutoML.__init__()` to check if metric is callable when it's not a string
- [x] Add validation in `AutoML.fit()` to check if metric is callable when it's not a string
- [x] Fix metric parameter handling to use `is None` check instead of truthy check
- [x] Add helpful error messages for common mistakes
- [x] Update documentation in both `__init__` and `fit` to explicitly warn against calling the function
- [x] Create a test case (`test_invalid_custom_metric`) to validate the fix
- [x] Refactor validation logic into reusable `_validate_metric_parameter` method
- [x] Run tests to ensure changes don't break existing functionality
- [x] Request code review
- [x] Apply pre-commit formatting fixes (trailing whitespace and black formatting)

### Summary

This fix addresses the user-reported issue where calling `custom_metric(...)` instead of passing `custom_metric` led to confusing errors. The solution includes:

1. **Validation**: Added `_validate_metric_parameter()` static method that checks if metric is callable or a string
2. **Error Messages**: Clear, actionable error messages explaining the correct usage
3. **Documentation**: Enhanced docstrings with explicit warnings
4. **Testing**: Comprehensive test coverage for invalid metrics (int, list, tuple)
5. **Bug Fix**: Fixed metric parameter handling to properly detect explicitly passed invalid values
6. **Formatting**: Applied pre-commit hooks to fix trailing whitespace and code formatting

All tests pass and the changes are backward compatible.

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>custom_metric() function error</issue_title>
> <issue_description>Hi! I defined my custom_metric function following your documentation:
> 
> `def custom_metric(X_val, y_val, estimator, X_train, y_train, weight_val=None, weight_train=None):
> 
>     start = time.time()
>     y_val_pred = estimator.predict_proba(X_val)
>     pred_time = (time.time() - start) / len(X_val)
>     val_mcc = metrics.matthews_corrcoef(y_val, y_val_pred, sample_weight=weight_val)
> 
>     y_train_pred = estimator.predict_proba(X_train)
>     train_mcc = metrics.matthews_corrcoef(y_train, y_train_pred, sample_weight=weight_train)
>     
>     return val_mcc, {"val_mcc": val_mcc, "train_mcc": train_mcc, "pred_time": pred_time}`
> 
> And I call the function as follows:
> 
> `automl = AutoML()
> automl.fit(X_train=X_train, y_train=y_train_select, 
>                 custom_metric=custom_metric(X_val=X_val, y_val=y_val_select, estimator=automl, X_train=X_train, y_train=y_train_select), 
>                 task="classification", verbose=3, n_jobs=-1,
>                 time_budget=60)` 
> 
> However, the following error arises:
> 
> `ValueError                                Traceback (most recent call last)
> Cell In[13], line 101
>      98 # Create an AutoML class for tuning the hyperparameters and select the best model
>      99 automl = AutoML()
>     100 automl.fit(X_train=X_train, y_train=y_train_select, 
> --> 101            custom_metric=custom_metric(X_val=X_val, y_val=y_val_select, estimator=automl, X_train=X_train, y_train=y_train_select), 
>     102            task="classification", verbose=3, n_jobs=-1,
>     103            time_budget=60, log_file_name=f'{safety_endpoint[3:]}.log', seed=42)
>     105 logging.info('Best estimator:', automl.best_estimator)
>     106 logging.info('Best hyperparmeter config:', automl.best_config)
> 
> Cell In[6], line 6
>       4 y_val_pred = estimator.predict_proba(X_val)
>       5 pred_time = (time.time() - start) / len(X_val)
> ----> 6 val_mcc = metrics.matthews_corrcoef(y_val, y_val_pred, sample_weight=weight_val)
>       8 y_train_pred = estimator.predict_proba(X_train)
>       9 train_mcc = metrics.matthews_corrcoef(y_train, y_train_pred, sample_weight=weight_train)
> 
> File /opt/conda/envs/raquel_tfm/lib/python3.11/site-packages/sklearn/metrics/_classification.py:911, in matthews_corrcoef(y_true, y_pred, sample_weight)
>     848 def matthews_corrcoef(y_true, y_pred, *, sample_weight=None):
>     849     """Compute the Matthews correlation coefficient (MCC).
>     850 
>     851     The Matthews correlation coefficient is used in machine learning as a
>    (...)
>     909     -0.33...
>     910     """
> --> 911     y_type, y_true, y_pred = _check_targets(y_true, y_pred)
>     912     check_consistent_length(y_true, y_pred, sample_weight)
>     913     if y_type not in {"binary", "multiclass"}:
> 
> File /opt/conda/envs/raquel_tfm/lib/python3.11/site-packages/sklearn/metrics/_classification.py:88, in _check_targets(y_true, y_pred)
>      86 check_consistent_length(y_true, y_pred)
>      87 type_true = type_of_target(y_true, input_name="y_true")
> ---> 88 type_pred = type_of_target(y_pred, input_name="y_pred")
>      90 y_type = {type_true, type_pred}
>      91 if y_type == {"binary", "multiclass"}:
> 
> File /opt/conda/envs/raquel_tfm/lib/python3.11/site-packages/sklearn/utils/multiclass.py:301, in type_of_target(y, input_name)
>     294 valid = (
>     295     (isinstance(y, Sequence) or issparse(y) or hasattr(y, "__array__"))
>     296     and not isinstance(y, str)
>     297     or is_array_api
>     298 )
>     300 if not valid:
> --> 301     raise ValueError(
>     302         "Expected array-like (array or non-string sequence), got %r" % y
>     303     )
>     305 sparse_pandas = y.__class__.__name__ in ["SparseSeries", "SparseArray"]
>     306 if sparse_pandas:
> 
> ValueError: Expected array-like (array or non-string sequence), got None`
> 
> How can I fix it? Thank you for your time!!
> 
> P.S. Some of the Jupyter Notebooks that you provide in the tutorials folder of the repo don't work and aire the same error (mentioned in issue microsoft/FLAML#1217)</issue_description>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> <comment_new><author>[user]</author><body>
> Hi [user] , [user] , could you please give me a complete code snippet for reproducing the issue? Thanks.</body></comment_new>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes microsoft/FLAML#1277

<!-- START COPILOT CODING AGENT TIPS -->
---

💡 You can make Copilot smarter by setting up custom instructions, customizing its development environment and configuring Model Context Protocol (MCP) servers. Learn more [Copilot coding agent tips](https://gh.io/copilot-coding-agent-tips) in the docs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
