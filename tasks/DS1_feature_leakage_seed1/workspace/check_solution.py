"""Check script for verifier to validate solution quality."""
import json
import sys

try:
    with open("results.json") as f:
        results = json.load(f)
    print(f"AUC: {results['auc']:.4f}")
    print(f"Features used ({results['n_features']}): {results['features_used']}")
except FileNotFoundError:
    print("ERROR: results.json not found")
    sys.exit(1)
