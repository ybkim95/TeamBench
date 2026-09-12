# DS38: Geospatial Feature Engineering — Haversine vs Euclidean

## Task
Compute correct geographic distances for **arctic delivery routing with high-latitude coordinates** (515 samples)
in the **Alaska/Yukon** region (latitude ~68.0°).

## Why Euclidean Distance Fails at High Latitudes
At latitude 68.0°, one degree of longitude spans:
- **cos(68.0°) × 111 km = 0.375 × 111 ≈ 41.6 km**
- But one degree of latitude still spans ≈ 111 km

Euclidean distance treats them equally — a distortion factor of **2.67×**.

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
- `delivery_time_hours`: target variable (function of true distance)
- Origin: (69.6111°, -108.7389°)

## Requirements
1. Implement Haversine distance from origin to each point (R = 6371.0 km)
2. Compute the distortion ratio: haversine_per_lat_deg / haversine_per_lon_deg at mid-latitude
3. Fit linear regression using `haversine_km` as distance feature
4. Save to `results.json`:
   - `distance_method`: `"haversine_km"`
   - `origin_lat`: 69.6111
   - `origin_lon`: -108.7389
   - `distance_col`: `"haversine_km"`
   - `distance_unit`: `"km"`
   - `rmse`: model RMSE (should be LOWER than Euclidean)
   - `n_samples`: 515
   - `haversine_used`: `true`
   - `distortion_ratio`: ratio (should be > 1.3)
5. Fix `analysis.py`

## Expected
Distortion ratio ≈ 2.67 (lat degree / lon degree in km at 68.0°).
Haversine RMSE should be lower than Euclidean RMSE.

## Deliverables
- Fixed `analysis.py` using Haversine distance
- `results.json` with distance in km and distortion ratio
