"""
Marketing attribution model for B2B SaaS pipeline marketing attribution.
BUG: Uses last-touch attribution — 100% credit goes to the LAST channel in
each converted journey. This ignores all earlier touchpoints that built
awareness and consideration, over-crediting closing channels.

Fix: Implement Shapley value attribution using marginal contributions:
- For each channel, compute its marginal contribution across all journey subsets
- Or use position-weighted approximation: first/last 40% each, middle 20% split
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/customer_journeys.csv")
CHANNELS = ['content', 'webinar', 'paid_search', 'demo_request', 'sales_outreach']

attribution = {ch: 0.0 for ch in CHANNELS}

converted = df[df["converted"] == 1]
n_converted = len(converted)

for _, row in converted.iterrows():
    touches = str(row["touchpoints"]).split("|")
    # BUG: last-touch attribution — only credit the final channel
    last_channel = touches[-1]
    if last_channel in attribution:
        attribution[last_channel] += 1.0

# BUG: normalize by n_converted gives last-touch fractions
if n_converted > 0:
    attribution = {k: round(v / n_converted, 4) for k, v in attribution.items()}

results = {
    "n_journeys": len(df),
    "n_converted": n_converted,
    "attribution_model": "last_touch",   # BUG: should be shapley
    "shapley_used": False,               # BUG: should be True
    "attribution": attribution,
    "top_channel": max(attribution, key=attribution.get) if attribution else None,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Attribution model: last_touch (WARNING: position-biased)")
print(f"Top channel: {results['top_channel']}")
