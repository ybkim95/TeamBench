"""
Feature importance analysis for customer churn prediction feature importance analysis.
BUG: Reports only MDI (Mean Decrease in Impurity) from tree feature_importances_.
MDI is BIASED toward high-cardinality features like `account_id_hash` which has
many unique values — these get more splits even if they carry no signal.

Fix:
1. Compute MDI importance (tree impurity-based)
2. Compute permutation importance (model-agnostic, unbiased)
3. Compute approximate SHAP values (TreeExplainer or linear SHAP approximation)
4. Compare rankings across methods
5. Flag features where methods disagree (rank difference > 2)
6. Report consensus ranking
"""
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("data/dataset.csv")
target_col = "churned"
feature_names = ['tenure_months', 'monthly_charges', 'contract_type', 'num_support_calls', 'payment_method_code', 'account_id_hash']

X = df[feature_names].values
y = df[target_col].values

# BUG: only MDI importance — biased toward high-cardinality features
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)

mdi_importances = rf.feature_importances_
mdi_ranking = list(np.argsort(-mdi_importances))
mdi_rank_names = [feature_names[i] for i in mdi_ranking]

results = {
    "mdi_importances": dict(zip(feature_names, [float(v) for v in mdi_importances])),
    "mdi_ranking": mdi_rank_names,
    "permutation_importances": None,   # BUG: not computed
    "shap_importances": None,           # BUG: not computed
    "consensus_ranking": mdi_rank_names,  # BUG: MDI only
    "disagreements": [],               # BUG: no comparison done
    "method": "mdi_only",             # BUG: should be "multi_method"
    "n_samples": len(df),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("MDI ranking:", mdi_rank_names)
print(f"WARNING: MDI may falsely rank `account_id_hash` high due to high cardinality!")
print("Saved results.json")
