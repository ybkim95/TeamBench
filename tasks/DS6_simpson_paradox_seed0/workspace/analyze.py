"""
Analysis script for drug treatment efficacy study.
BUG: Only computes aggregate statistics — misses Simpson's Paradox.
Fix: Analyze by subgroup (severity) to find the true relationship.
"""
import pandas as pd
import json

df = pd.read_csv("data/study_data.csv")

# BUG: Aggregate analysis only — wrong conclusion
agg = df.groupby("treatment")["recovery_rate"].mean()
print("Aggregate recovery_rate by treatment:")
print(agg)

# BUG: Conclusion based only on aggregate
winner = agg.idxmax()
print(f"\nConclusion: {winner} has higher recovery_rate")

results = {
    "aggregate_analysis": agg.to_dict(),
    "conclusion": winner,
    "subgroup_analysis": None,  # BUG: missing subgroup breakdown
    "confound_checked": False,  # BUG: should be True
    "correct_analysis_level": None,  # BUG: should be "severity"
}
with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved analysis_results.json")
