"""
Schema migration for IoT sensor data schema evolution.
BUG 1: Renames columns but does NOT write alias metadata, breaking old-schema readers.
BUG 2: Uses narrow type casting (astype int32/float32) instead of widening to int64/float64.
BUG 3: New nullable columns filled with 0 instead of None/NaN.

Fix:
1. Write aliases dict to output metadata (new_name -> old_name mapping)
2. Use widened types (int64, float64) not narrow types
3. Fill new nullable columns with None/NaN
"""
import pandas as pd
import json

df = pd.read_csv("data/old_data.csv")
with open("schema_old.json") as f:
    old_schema = json.load(f)
with open("schema_new.json") as f:
    new_schema_def = json.load(f)

renames = {'sid': 'sensor_id', 't': 'epoch_ms', 'temp': 'temperature_c'}
widenings = {'sensor_id': 'int64', 'epoch_ms': 'int64'}

# Apply renames
df = df.rename(columns=renames)

# BUG: narrow type casting instead of widening
for col, new_type in widenings.items():
    if col in df.columns:
        if "int" in new_type:
            df[col] = df[col].astype("int32")   # BUG: should be int64
        elif "float" in new_type:
            df[col] = df[col].astype("float32") # BUG: should be float64

# Add new nullable columns
for col_name in ['battery_pct']:
    df[col_name] = 0  # BUG: should be None/NaN for nullable

results = {
    "n_records": len(df),
    "columns": list(df.columns),
    "aliases_written": False,  # BUG: should be True
    "types_widened": False,    # BUG: should be True
    "nullable_columns_null": False,  # BUG: should be True
    "dtypes": {col: str(df[col].dtype) for col in df.columns},
}
df.to_csv("data/migrated_data.csv", index=False)
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Migrated {len(df)} records. WARNING: schema not backward compatible!")
