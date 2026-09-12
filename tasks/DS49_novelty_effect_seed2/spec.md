# DS49: Experiment Novelty Effect Correction

## Task
Analyze an A/B test of notification system A/B test with novelty effect over **12 weeks**.
The treatment shows a **novelty effect** that decays over time.

## The Problem: Novelty Effect Decay
Users open new notification styles more frequently at first.
The weekly treatment effect follows an exponential decay:
```
weekly_effect(w) = steady_state + novelty_boost × exp(-0.5 × (w-1))
```
- Early weeks: effect ≈ 0.1469 (inflated by novelty)
- Steady state: effect ≈ 0.0134
- Decay period: first ~5 weeks

Naive analysis averaging all weeks overstates the long-run effect.

## Correction Method
1. Observe that `weekly_effect` decreases in early weeks and stabilizes
2. Find `stabilization_week`: first week where effect is within 50% of the
   minimum observed weekly effect (or fit exponential decay)
3. Report average effect from `stabilization_week` onwards

## Data
File: `data/ab_test_weekly.csv`
- `week`: week number (1 to 12)
- `n_control`, `n_treatment`: user counts per group
- `control_open_rate`, `treatment_open_rate`: metric rates
- `weekly_effect`: pre-computed treatment effect per week

## Requirements
1. Load `data/ab_test_weekly.csv`
2. Detect stabilization: find the week where `weekly_effect` first stabilizes
   (hint: stabilization_week ≈ 7)
3. Compute steady-state effect as mean of `weekly_effect` from stabilization_week onward
4. Save to `results.json`:
   - `stabilization_week`: detected week (should be ≈ 7)
   - `novelty_corrected`: `true`
   - `treatment_effect`: steady-state effect (post-decay weeks only)
   - `n_weeks_used`: number of post-decay weeks used
5. Fix `ab_analysis.py`

## Expected Results
- Naive (all weeks) effect ≈ 0.0416 (overstated)
- Correct (post-decay) effect ≈ 0.0161

## Deliverables
- Fixed `ab_analysis.py`
- `results.json` with novelty-corrected treatment effect
