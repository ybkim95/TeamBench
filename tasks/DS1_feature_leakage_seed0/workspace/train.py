"""
Classifier training script.

The dataset contains features that are suspicious — some may leak target information.
Current code uses ALL features including leaky ones (near-perfect AUC due to leakage).

TASK: Identify and exclude the truly leaky features.
NOTE: Not all correlated features are leaky. Some are legitimate predictors.
      #  predictors will LOWER model AUC.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import json

df = pd.read_csv("data/dataset.csv")
TARGET = "defaulted"

# Current code uses ALL features — includes both leaky and legitimate ones
# TODO: Replace with the correct feature set per the spec
all_features = ['income', 'employment_years', 'num_credit_lines', 'monthly_expenses', 'zip_region_code', 'debt_ratio', 'credit_score_prev', 'num_late_payments_prev', 'payment_status_after_1month', 'days_past_due_final', 'internal_risk_score', 'loan_outcome_code']

feature_cols = [c for c in all_features if c in df.columns and c != TARGET and c != "id"]

X = df[feature_cols].replace("", -1).fillna(-1)
y = df[TARGET].astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred)
print(f"Test AUC: {auc:.4f}")

results = {
    "auc": float(auc),
    "features_used": feature_cols,
    "n_features": len(feature_cols),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved results.json")
