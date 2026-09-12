"""
Data contract validator for user registration data contract validation.
BUG: Uses overly permissive regex that misses many semantic violations:
  - Email: accepts "user@" (no TLD check) and "user@domain" (no dot required)
  - Phone: accepts "14155552671" (no + prefix check)
  - Currency: accepts "usd" (case-insensitive, should be uppercase only)
  - UUID: accepts any hex string without version/variant checks
  - Amount: accepts negative numbers and extra decimal places

Fix: Implement strict semantic type validators per the contract spec:
  - email: must match r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
  - phone: must match r"\+[1-9]\d{6,14}"
  - currency: must match r"[A-Z]{3}" (uppercase only)
  - uuid4: must match version 4 format with variant bits
  - amount: must be >= 0 and have at most 2 decimal places
"""
import pandas as pd
import json
import re

df = pd.read_csv("data/dataset.csv")
with open("contract.json") as f:
    contract = json.load(f)

# BUG: overly permissive validators
def validate_field(value, field_type):
    v = str(value).strip()
    if field_type == "email_rfc5321":
        return bool(re.match(r".+@.+", v))           # BUG: too permissive
    elif field_type == "e164_phone":
        return bool(re.match(r"[+0-9]{7,}", v))    # BUG: accepts without +, accepts 00-prefix
    elif field_type == "iso4217":
        return bool(re.match(r"[a-zA-Z]{3}", v))   # BUG: accepts lowercase
    elif field_type == "uuid4":
        return bool(re.match(r"[0-9a-f-]{32,}", v.lower()))  # BUG: no version/variant check
    elif field_type == "monetary_nonneg":
        try:
            return float(v) >= -999999  # BUG: accepts negatives
        except ValueError:
            return False
    elif field_type == "iso_date":
        return bool(re.match(r"\d{4}-\d{2}-\d{2}", v))
    elif field_type == "iso3166_alpha2":
        return bool(re.match(r"[a-zA-Z]{2}", v))   # BUG: accepts lowercase
    return True

fields = [('user_id', 'uuid4'), ('email', 'email_rfc5321'), ('phone', 'e164_phone'), ('signup_date', 'iso_date'), ('country_code', 'iso3166_alpha2')]

violations = []
for _, row in df.iterrows():
    for field_name, field_type in fields:
        val = row.get(field_name, "")
        if not validate_field(val, field_type):
            violations.append({
                "record_id": int(row["record_id"]),
                "field": field_name,
                "value": str(val),
                "type": field_type,
            })

results = {
    "total_records": len(df),
    "violations_found": len(violations),
    "strict_validation": False,  # BUG: should be True
    "violations": violations,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Checked {len(df)} records, found {len(violations)} violations")
print("WARNING: Validation may miss violations due to permissive regex!")
