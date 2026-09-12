# DS44: Attribution Model Position Bias (Shapley Values)

## Task
Compute **Shapley value attribution** for B2B SaaS pipeline marketing attribution across
**268 customer journeys**.

## The Problem: Last-Touch Bias
Last-touch attribution gives 100% credit to the final touchpoint. This:
- Over-credits "closing" channels (e.g., branded search, direct)
- Under-credits "awareness" channels (e.g., display, content)
- Leads to incorrect budget allocation decisions

## Shapley Value Attribution
Shapley values fairly distribute credit based on marginal contribution.
For marketing attribution, use position-weighted Shapley:
- First touch: 40% of credit
- Last touch: 40% of credit
- Middle touches: 20% split equally

For single-channel journeys: 100% to that channel.

## Data
File: `data/customer_journeys.csv`
- `journey_id`: journey identifier
- `touchpoints`: pipe-separated channel sequence (e.g., `"display|email|branded_search"`)
- `converted`: 1 if journey converted, 0 otherwise
- `revenue`: revenue from conversion (0 if not converted)

## Requirements
1. Load `data/customer_journeys.csv`
2. Filter to converted journeys only
3. For each converted journey, compute Shapley weights per channel:
   - Single channel: weight = 1.0
   - Multi-channel: first=0.4, last=0.4, middle=(0.2 / n_middle) each
4. Sum Shapley credits per channel across all converted journeys
5. Normalize by n_converted to get average attribution fraction
6. Save to `results.json`:
   - `attribution_model`: `"shapley"`
   - `shapley_used`: `true`
   - `attribution`: dict channel -> Shapley fraction
   - `top_channel`: channel with highest Shapley credit
7. Fix `attribution.py`

## Expected Results
- Top Shapley channel: `paid_search` (Shapley ≈ 0.217)
- Top last-touch channel: `paid_search` (last-touch ≈ 0.217)
- Note: these may differ significantly, showing attribution bias

## Deliverables
- Fixed `attribution.py`
- `results.json` with Shapley attribution values
