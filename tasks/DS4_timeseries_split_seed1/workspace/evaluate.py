"""
Model evaluation script for power grid demand forecasting with 3 model types.

Three models are being evaluated with different feature sets.
The cross-validation strategy is currently WRONG for all three.

Issue: All 3 models use KFold — but each model has different data characteristics
that require a different CV approach. Read the spec before fixing.

IMPORTANT: Not all models need TimeSeriesSplit. Read the data characteristics first.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import roc_auc_score
import json

df = pd.read_csv("data/timeseries.csv")
df = df.sort_values("timestamp").reset_index(drop=True)

TARGET = "demand_high"
TIME_COL = "timestamp"
ENTITY_COL = "grid_zone"
GROUP_COL = "region_id"

features_a = ['hour_lag1', 'hour_lag24', 'hour_lag168', 'rolling_7d_mean', 'trend_index']
features_b = ['temperature_c', 'humidity_pct', 'cloud_cover_pct', 'wind_speed_ms']
features_c = ['zone_capacity_pct', 'neighbour_demand', 'grid_frequency', 'import_export_mw']

model = GradientBoostingClassifier(n_estimators=50, random_state=42)

# BUG: All models use the same KFold — wrong for models with temporal/group structure
# Each model requires a different CV strategy based on its data characteristics
cv = KFold(n_splits=5, shuffle=True, random_state=42)

X_a = df[features_a].values
X_b = df[features_b].values
X_c = df[features_c].values
y = df[TARGET].astype(int).values
groups = df[GROUP_COL].values

scores_a = cross_val_score(model, X_a, y, cv=cv, scoring="roc_auc")
scores_b = cross_val_score(model, X_b, y, cv=cv, scoring="roc_auc")
scores_c = cross_val_score(model, X_c, y, cv=cv, scoring="roc_auc")

results = {
    "model_a_cv": "KFold",        # BUG: wrong for model A
    "model_b_cv": "KFold",        # May or may not need changing — check spec
    "model_c_cv": "KFold",        # BUG: wrong for model C
    "model_a_mean_auc": float(scores_a.mean()),
    "model_b_mean_auc": float(scores_b.mean()),
    "model_c_mean_auc": float(scores_c.mean()),
    "model_a_scores": scores_a.tolist(),
    "model_b_scores": scores_b.tolist(),
    "model_c_scores": scores_c.tolist(),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved results.json")
