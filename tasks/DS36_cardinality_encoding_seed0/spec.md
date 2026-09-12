# DS36: Cardinality-Aware Encoding Strategy

## Task
Apply **cardinality-appropriate encoding** for **retail transaction value prediction** (994 samples).

## The Problem
One-hot encoding ALL features creates 59 columns total.
High-cardinality features create many sparse columns where each category
appears rarely, leading to overfitting and poor generalization.

## Cardinality Tiers and Encoding Strategy
| Feature | Cardinality | Tier | Correct Encoding |
|---------|-------------|------|-----------------|
| `payment_type` | 3 | low | one hot |
| `product_category` | 8 | medium | target encoding |
| `store_id` | 45 | high | target encoding smoothed |

**Rules**:
- Low cardinality (< 5): one-hot encoding
- Medium cardinality (5–20): target encoding (train-only mean ± smoothing)
- High cardinality (> 20): target encoding with **smoothing** (k=10):
  ```python
  smooth_k = 10
  global_mean = train[target_col].mean()
  enc = (cat_sum + smooth_k * global_mean) / (cat_count + smooth_k)
  ```

## Data
File: `data/dataset.csv`
- Target: `purchase_amount`
- Categorical features: `['payment_type', 'product_category', 'store_id']`
- Numeric features: `['quantity', 'discount_pct', 'customer_age']`

## Requirements
1. Compute cardinality for each categorical feature
2. Apply encoding based on cardinality tier (thresholds: low < 5, high > 20)
3. For target encoding: fit on train split only (first 80% of data)
4. Fit linear regression on encoded features
5. Save to `results.json`:
   - `encoding_strategy`: dict mapping feature name → encoding method used
   - `n_features_after_encoding`: total feature count (should be << 59)
   - `encoding_method`: `"cardinality_aware"`
   - `r2`: R² of model
   - `n_samples`: 994
   - `cardinalities`: dict of feature → unique count
   - `low_card_threshold`: 5
   - `high_card_threshold`: 20
6. Fix `analysis.py`

## Expected Encoding Strategy
{'payment_type': 'one_hot', 'product_category': 'target_encoding', 'store_id': 'target_encoding_smoothed'}

## Deliverables
- Fixed `analysis.py` with cardinality-aware encoding
- `results.json` with encoding strategy per feature
