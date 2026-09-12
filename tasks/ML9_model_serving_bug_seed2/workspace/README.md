# ML9: Model Serving Bug — Image Model Serving With Normalization And Shape Bugs

The inference pipeline has preprocessing inconsistencies with the training pipeline.

## Task
1. Run `python train_model.py` first (generates model and reference predictions)
2. Fix `serve.py` so inference output matches training output
3. Run `python serve.py` then `python check_serving.py`
