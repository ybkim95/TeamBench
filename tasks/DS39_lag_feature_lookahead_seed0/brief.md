# DS39: Lag Feature Look-Ahead Bias (Brief)

Fix lag features for stock return prediction with lag features.
Dataset: `data/timeseries.csv`
Fix `analysis.py`: use shift() not rolling(center=True); drop NaN warmup rows.
Save results to `results.json`.
