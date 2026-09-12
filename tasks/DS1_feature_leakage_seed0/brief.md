# DS1: Feature Leakage Detection (Brief)

Build a binary classifier for loan applicant credit default prediction.
Target variable: `defaulted`
Dataset: `data/dataset.csv`

The dataset contains some columns that may be problematic due to data leakage.
Identify the leaky features and train a model on the clean feature set.

Save AUC and feature list to `results.json`.
Script: `train.py`
