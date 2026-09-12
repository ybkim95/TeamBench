# DS31: Target Encoding — Train/Test Leakage

## Task
Fix target encoding for **e-commerce click-through rate prediction** (1194 samples).
The current script leaks test-set information into features.

## The Bug
The script computes `df.groupby('product_category')['clicked'].mean()` on the **full dataset**
before splitting into train/test. This means test-set target values influence
the encoding, creating data leakage that artificially inflates test metrics.

## Why This Matters
When the test set's targets are included in computing category means:
- Categories with high test-set target rates get inflated encodings
- The model "sees" the test targets through the encoded feature
- Test performance metrics are optimistically biased

## Correct Approach
1. Split train/test **first**: `train = df.iloc[:896]`, `test = df.iloc[896:]`
2. Compute target encoding statistics on **TRAIN set only**:
   ```python
   global_mean = train['clicked'].mean()
   cat_means = train.groupby('product_category')['clicked'].mean()
   ```
3. Apply **smoothing** (Laplace/additive) to handle rare categories:
   ```python
   smooth_k = 20
   cat_encoding = (cat_sums + smooth_k * global_mean) / (cat_counts + smooth_k)
   ```
4. Transform test set using the **train-derived** encoding (not test stats)

## Data
File: `data/dataset.csv`
- `clicked`: binary target (0/1)
- `product_category`: categorical feature to encode
- Numeric features: `['price', 'page_views', 'time_on_site']`
- First 896 rows = train, remaining 298 rows = test

## Requirements
Save to `results.json`:
- `global_mean`: train-set target mean
- `category_encodings`: dict of train-only smoothed encodings
- `encoding_method`: `"train_only"`
- `test_correlation`: test set prediction correlation (should be LOWER than leaky version)
- `n_train`: 896
- `n_test`: 298
- `leakage_present`: `false`

## Expected Train Encodings (first 3 categories, smoothed)
{'sports': 0.2383, 'books': 0.2465, 'clothing': 0.2484}

## Deliverables
- Fixed `analysis.py`
- `results.json` with train-only target encoding
