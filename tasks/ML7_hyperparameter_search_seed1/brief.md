# ML7: Hyperparameter Search (Brief)

## Your Task
Fix the hyperparameter search for **gradient boosting with invalid hyperparameter combinations**.

The current search space includes invalid parameter combinations that either
crash the model, produce undefined behavior, or waste compute on impossible configs.

## What You Know
- Search code is in `hyperparameter_search.py`
- There are **3 invalid parameter issues** in the search space
- The Planner has the valid search space specification
- After fixing, run `python hyperparameter_search.py` then `python check_search.py`

## Rules
- Fix only `hyperparameter_search.py`
- Do not modify `check_search.py`
- Goal: zero invalid combinations tried, best accuracy > 0.5
