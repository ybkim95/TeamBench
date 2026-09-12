"""
Data cleaning script for network packet capture anomaly dataset.

The anomaly detector has flagged 6 outlier groups. Current script removes ALL flagged rows.

TASK: Apply the correct treatment for EACH group based on domain knowledge.
NOTE: Not all outlier groups should be removed. Read the spec carefully.
      Removing signal groups REDUCES the score.
      Removing the ambiguous group (group 6) also REDUCES the score.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/dataset.csv")
print(f"Original rows: {len(df)}")
print(f"Outlier group distribution:")
print(df["outlier_group"].value_counts())

# BUG: Removes ALL flagged rows including genuine signals
# Current logic: remove anything not in "normal" group
df_clean = df[df["outlier_group"] == "normal"].copy()

# BUG: Group 3 (ddos_amplification) uses wrong detector threshold
# Current threshold removes values in range (3000, 55000)
# but the correct threshold per the spec is different

# BUG: Group 6 should be flagged with indicator column, not removed

print(f"After cleaning: {len(df_clean)} rows")
df_clean.to_csv("data/cleaned.csv", index=False)

stats = {
    "original_rows": len(df),
    "cleaned_rows": len(df_clean),
    "removed_rows": len(df) - len(df_clean),
    "group_counts_removed": df[df["outlier_group"] != "normal"]["outlier_group"].value_counts().to_dict(),
    "tls_unknown_flag_flagged": 0,  # BUG: should flag group 6 rows, not remove them
}
with open("cleaning_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print("Saved cleaned.csv and cleaning_stats.json")
