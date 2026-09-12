# DS30: Data Contract Validation with Semantic Types

## Task
Validate 60 records from product catalog data contract validation against a data contract
with **semantic type constraints** stricter than simple dtype checks.

## Contract Fields
| Field | Semantic Type |
|-------|---------------|
| `sku` | `uuid4` |
| `price` | `monetary_nonneg` |
| `currency` | `iso4217` |
| `supplier_email` | `email_rfc5321` |
| `supplier_phone` | `e164_phone` |

## Semantic Type Rules
| Type | Rule |
|------|------|
| `email_rfc5321` | Must match `[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}` |
| `e164_phone` | Must start with `+`, followed by 6-14 digits, first digit non-zero |
| `uuid4` | Must be `xxxxxxxx-xxxx-4xxx-[89ab]xxx-xxxxxxxxxxxx` (version 4, variant bits) |
| `iso4217` | Exactly 3 **uppercase** letters (e.g., `USD`, not `usd`) |
| `monetary_nonneg` | Float ≥ 0, max 2 decimal places |
| `iso_date` | `YYYY-MM-DD` format |
| `iso3166_alpha2` | Exactly 2 **uppercase** letters (e.g., `US`, not `us`) |

## Known Invalid Examples
- Email: `user@` (no TLD), `user@domain` (no dot), `bad email@x.com` (space)
- Phone: `14155552671` (no +), `+0123456789` (starts with 0), `555-1234` (local format)
- Currency: `usd` (lowercase), `USDD` (4 letters)
- UUID: `not-a-uuid`, version-3 UUIDs

## Requirements
1. Load `data/dataset.csv` and `contract.json`
2. For each record, validate each field against its semantic type
3. Collect all violations as list of `{record_id, field, value, type}`
4. Save to `results.json`:
   - `total_records`: 60
   - `violations_found`: count of violations (expected ~15 records with violations)
   - `strict_validation`: `true`
   - `violations`: list of violation dicts
5. Fix `validate.py`

## Deliverables
- Fixed `validate.py` with strict semantic validators
- `results.json`
