"""
Geospatial feature engineering for Scandinavian route time prediction.
BUG: Uses Euclidean distance on raw lat/lon coordinates.
At latitude 62.5°, longitude degrees are much shorter
than latitude degrees (by factor of cos(62.5°) ≈ 0.462).
This creates severe distortion in distance calculations.

Fix: Use Haversine formula for great-circle distance:
  a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
  distance = 2 * R * asin(sqrt(a))  where R = 6371 km
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/locations.csv")
target_col = "route_time_min"
origin_lat = 64.32177220271969
origin_lon = 14.780958820970294

# BUG: Euclidean distance in degree-space ignores latitude compression
df["distance"] = np.sqrt(
    (df["latitude"] - origin_lat)**2 +
    (df["longitude"] - origin_lon)**2
)

# BUG: distance is in degrees, not km, and is distorted at high latitudes
X = df[["distance"]].values
y = df[target_col].values
n = len(y)

from numpy.linalg import lstsq
coef, _, _, _ = lstsq(np.column_stack([np.ones(n), X]), y, rcond=None)
y_pred = np.column_stack([np.ones(n), X]) @ coef
rmse = float(np.sqrt(np.mean((y - y_pred)**2)))

results = {
    "distance_method": "euclidean_degrees",  # BUG: should be "haversine_km"
    "origin_lat": origin_lat,
    "origin_lon": origin_lon,
    "distance_col": "distance",
    "distance_unit": "degrees",  # BUG: should be "km"
    "rmse": rmse,
    "n_samples": n,
    "haversine_used": False,  # BUG
    "distortion_ratio": None,  # BUG: not computed
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Euclidean distance (degrees) RMSE: {rmse:.4f}")
print("WARNING: Euclidean degrees distorted at high latitude!")
print("Saved results.json")
