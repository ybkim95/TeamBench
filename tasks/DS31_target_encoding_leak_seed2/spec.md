# DS31: Target Encoding — Train/Test Leakage

## Task
Fix target encoding for **employee attrition prediction by department** (857 samples).
The current script leaks test-set information into features.

## The Bug
The script computes `df.groupby('department')['left_company'].mean()` on the **full dataset**
before splitting into train/test. This means test-set target values influence
the encoding, creating data leakage that artificially inflates test metrics.

## Why This Matters
When the test set's targets are included in computing category means:
- Categories with high test-set target rates get inflated encodings
- The model "sees" the test targets through the encoded feature
- Test performance metrics are optimistically biased

## Correct Approach
1. Split train/test **first**: `train = df.iloc[:643]`, `test = df.iloc[643:]`
2. Compute target encoding statistics on **TRAIN set only**:
   ```python
   global_mean = train['left_company'].mean()
   cat_means = train.groupby('department')['left_company'].mean()
   ```
3. Apply **smoothing** (Laplace/additive) to handle rare categories:
   ```python
   smooth_k = 20
   cat_encoding = (cat_sums + smooth_k * global_mean) / (cat_counts + smooth_k)
   ```
4. Transform test set using the **train-derived** encoding (not test stats)

## Data
File: `data/dataset.csv`
- `left_company`: binary target (0/1)
- `department`: categorical feature to encode
- Numeric features: `['salary', 'tenure_years', 'satisfaction_score']`
- First 643 rows = train, remaining 214 rows = test

## Requirements
Save to `results.json`:
- `global_mean`: train-set target mean
- `category_encodings`: dict of train-only smoothed encodings
- `encoding_method`: `"train_only"`
- `test_correlation`: test set prediction correlation (should be LOWER than leaky version)
- `n_train`: 643
- `n_test`: 214
- `leakage_present`: `false`

## Expected Train Encodings (first 3 categories, smoothed)
{'hr': 0.0868, 'operations': 0.1259, 'legal': 0.0643}

## Deliverables
- Fixed `analysis.py`
- `results.json` with train-only target encoding
