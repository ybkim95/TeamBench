# DS40: Business Calendar Date Features

## Task
Engineer business-calendar-aware date features for **financial transactions with fiscal year end March 31**
(720 daily observations).

## The Problem
Standard date decomposition (`year`, `month`, `day_of_week`, `calendar_quarter`)
misses critical business calendar signals:

1. **Fiscal quarter ≠ calendar quarter**: fiscal year starts in month 4
2. **Company holidays**: 5 holiday occurrences in the data drive demand spikes
3. **Days to quarter end**: proximity to fiscal quarter end correlates with target
4. **High season**: months [3, 4] have systematically higher values

## Fiscal Quarter Mapping
| Quarter | Months |
|---------|--------|
| Q1 | months [4, 5, 6] |
| Q2 | months [7, 8, 9] |
| Q3 | months [10, 11, 12] |
| Q4 | months [1, 2, 3] |

## Company Holidays
- FiscalYearEnd: month 3, day 31
- CalendarYearEnd: month 12, day 31
- FiscalYearStart: month 4, day 1

## High-Season Months
[3, 4]

## Data
File: `data/daily_data.csv`
Columns: `date`, `year`, `month`, `day`, `day_of_week`, `transaction_volume`

## Requirements
1. Add `fiscal_quarter` column: map each month to its fiscal quarter (`"Q1"`–`"Q4"`)
2. Add `is_company_holiday` column: 1 if (month, day) matches a company holiday, else 0
3. Add `days_to_fiscal_quarter_end` column:
   - Find the last month of the current fiscal quarter
   - Count days until the end of that month
4. Add `is_high_season` column: 1 if month in [3, 4], else 0
5. Fit linear regression using all 4 new features + original calendar features
6. Save to `results.json`:
   - `features_used`: list of all feature names
   - `fiscal_quarter_computed`: `true`
   - `is_company_holiday_computed`: `true`
   - `days_to_fiscal_quarter_end_computed`: `true`
   - `is_high_season_computed`: `true`
   - `rmse`: model RMSE (should be LOWER than calendar-only)
   - `n_samples`: 720
   - `fiscal_year_start_month`: 4
   - `n_holidays_flagged`: number of holiday rows (≈ 5)
7. Fix `analysis.py`

## Deliverables
- Fixed `analysis.py` with business calendar features
- `results.json` with all 4 new features computed
