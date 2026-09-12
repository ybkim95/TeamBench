# DS38: Geospatial Feature Engineering — Haversine vs Euclidean

## Task
Compute correct geographic distances for **Canadian logistics cost prediction** (591 samples)
in the **Canada** region (latitude ~54.5°).

## Why Euclidean Distance Fails at High Latitudes
At latitude 54.5°, one degree of longitude spans:
- **cos(54.5°) × 111 km = 0.581 × 111 ≈ 64.5 km**
- But one degree of latitude still spans ≈ 111 km

Euclidean distance treats them equally — a distortion factor of **1.72×**.

## Haversine Formula
```python
import numpy as np
def haversine(lat1, lon1, lat2, lon2, R=6371.0):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
```

## Data
File: `data/locations.csv`
- `latitude`, `longitude`: coordinates of each point
- `transport_cost_cad`: target variable (function of true distance)
- Origin: (52.2332°, -72.8705°)

## Requirements
1. Implement Haversine distance from origin to each point (R = 6371.0 km)
2. Compute the distortion ratio: haversine_per_lat_deg / haversine_per_lon_deg at mid-latitude
3. Fit linear regression using `haversine_km` as distance feature
4. Save to `results.json`:
   - `distance_method`: `"haversine_km"`
   - `origin_lat`: 52.2332
   - `origin_lon`: -72.8705
   - `distance_col`: `"haversine_km"`
   - `distance_unit`: `"km"`
   - `rmse`: model RMSE (should be LOWER than Euclidean)
   - `n_samples`: 591
   - `haversine_used`: `true`
   - `distortion_ratio`: ratio (should be > 1.3)
5. Fix `analysis.py`

## Expected
Distortion ratio ≈ 1.72 (lat degree / lon degree in km at 54.5°).
Haversine RMSE should be lower than Euclidean RMSE.

## Deliverables
- Fixed `analysis.py` using Haversine distance
- `results.json` with distance in km and distortion ratio
