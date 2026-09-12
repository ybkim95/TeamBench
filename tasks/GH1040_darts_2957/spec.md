# GH1040_darts_2957: Fix/tft explainer index error — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2955
- Repo: https://github.com/unit8co/darts

## Issue Description

### Background
I've built and trained a TFTModel on a long list of many independent timeseries objects, now I want to use the TFTExplainer as demonstrated in the docs https://unit8co.github.io/darts/examples/13-TFT-examples.html#Explainability. 

### Expected behavior
`TFTExplainer.explain()` should extract the relevant attention from the attention_matrix

### Actual behavior
`TFTExplainer.explain()` indexes the attention_heads using an incorrect index value, which comes from iterating over the list of timeseries objects. This crashes the `explain()` call with an `IndexError: index N is out of bounds for axis 0 with size N`

See https://github.com/unit8co/darts/blob/b1d45b54ee464b76cb0d7f149adbf08b219616ea/darts/explainability/tft_explainer.py#L218

This makes itself very apparent when the count of timeseries objects is greater than the size of the first axis of the attention_heads matrix

### To Reproduce

**1. Load a dataset with many timeseries in a list**

The TrafficDataset is useful, with 862 timeseries objects each spanning 17544 steps
 
```python
from darts.datasets import TrafficDataset
serieses = TrafficDataset(multivariate=False).load()
print(f"Imported list of {len(serieses)} timeseries objects")

import pandas as pd
pd.Series([len(ts) for ts in serieses]).value_counts()
```
> Imported list of 862 timeseries objects
> 17544 862



**2. Train model (note I convert to float32 because using Apple Silicon MPS)**

```python
def _to_float32(ts):
    import numpy as np
    """Helper function to convert TimeSeries to float32"""
    return ts.astype(np.float32) if hasattr(ts, "astype") else ts

serieses32 = [_to_float32(ts) for ts in serieses]

from darts.models import TFTModel

tft_model = TFTModel(
    input_chunk_length=12,
    output_chunk_length=6,
    add_encoders={"cyclic": {"future": ["month"]}},
    hidden_size=64, 
    lstm_layers=1,
    num_attention_heads=4,
    n_epochs=3,
    pl_trainer_kwargs = dict(
            precision="32-true",  # Force float32 for MPS compatibility
            accelerator="gpu",  # Use GPU (MPS on Apple Silicon)
            devices="auto",
            strategy="auto",
        ),
)
tft_model.fit(serieses32, verbose=True, max_samples_per_ts=10,
          dataloader_kwargs=dict(pin_memory=False))
```
> `Trainer.fit` stopped: `max_epochs=3` reached.
TFTModel(output_chunk_shift=0, hidden_size=64, lstm_layers=1, num_attention_heads=4, full_attention=False, feed_forward=GatedResidualNetwork, dropout=0.1, hidden_continuous_size=8, categorical_embedding_sizes=None, add_relative_index=False, skip_interpolation=False, loss_fn=None, likelihood=None, norm_type=LayerNorm, use_static_covariates=True, input_chunk_length=12, output_chunk_length=6, add_encoders={'cyclic': {'future': ['month']}}, n_epochs=3, pl_trainer_kwargs={'precision': '32-true', 'accelerator': 'gpu', 'devices': 'auto', 'strategy': 'auto'})


**3. Note the shape of the attention heads matrix**

To be used per https://github.com/unit8co/darts/blob/b1d45b54ee464b76cb0d7f149adbf08b219616ea/darts/explainability/tft_explainer.py#L204

```python
# shape is (???, output_chunk_len, num_attention_heads, input_chunk_length+output_chunk_len)
print(tft_model.model._attn_out_weights.detach().cpu().numpy().shape)
print(tft_model.model._attn_out_weights.detach().cpu().numpy().sum(axis=-2).shape)
```
> (30, 6, 4, 18)
> (30, 6, 18)

**4. Try to run the explainer**

```python
from darts.explainability.tft_explainer import TFTExplainer
explainer = TFTExplainer(tft_model, background_series=serieses32)
explanation = explainer.explain()
```

> IndexError
```
---------------------------------------------------------------------------
IndexError                                Traceback (most recent call last)
Cell In[8], line 3
      1 from darts.explainability.tft_explainer import TFTExplainer
      2 explainer = TFTExplainer(tft_model, background_series=serieses32)
----> 3 explanation = explainer.explain()

File ~/workspace/tft/.venv/lib/python3.12/site-packages/darts/explainability/tft_explainer.py:219, in TFTExplainer.explain(self, foreground_series, foreground_past_covariates, foreground_future_covariates, horizons, target_components)
    216 for idx, (series, pred_series) in enumerate(zip(foreground_series, preds)):
    217     times = series.time_index[-icl:].union(pred_series.time_index)
    218     attention = TimeSeries(
--> 219         values=np.take(attention_heads[idx], horizon_idx, axis=0).T,
    220         times=times,
    221         components=[f"horizon {str(i)}" for i in horizons],
    222     )
    223     results.append({
    224         "attention": attention,
    225         "encoder_importance": encoder_importance.iloc[idx : idx + 1],
   (...)    229         ],
    230     })
    231 return TFTExplainabilityResult(
    232     explanations=results[0] if len(results) == 1 else results
    233 )

IndexError: index 30 is out of bounds for axis 0 with size 30
```


### System (please complete the following information)
 - Python version: `3.12.10`
 - darts version `0.38.0`


### AOB

I hope this is just an indexing issue, but it seems to imply the first axis of the `attention_heads` matrix might not actually be what we think it is. Could you also confirm what it's expected to be? From the docs / papers, I'd expect it to be the Q vector, which ought not to have much to do with the list of timeseries, so I suspect the wrong iterable has been chosen inside TFTExplainer.explain() to index the attn_heads.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], and thanks for raising this issue. Don't worry, the model (and attention) is working as expected, only that we should raise an error when the user tries to explain more time series than the model's `batch_size`.

The attention heads have shape: `(last_batch_size, ...)`.
The last batch size is determined by the number of leftover samples to create the last batch (so that we include all possible samples in one epoch / inference process).

Now, when you're trying to `explain()`, the model is in inference mode and only one sample (the end of the series) will be extracted from each time series. If the number of series exceeds the batch size, the model runs inference in multiple steps until all batches were computed. For explanation, we only cache the attention weights of the last batch. This is why it threw an index error.

<details>

<summary>Here is a simplified example to showcase this behavior</summary>

```py
from darts.datasets import AirPassengersDataset
from darts.models import TFTModel
from darts.explainability import TFTExplainer

def get_attn_shape(model_):
    shape = model_.model._attn_out_weights.detach().cpu().numpy().shape
    print(shape)
    return shape

series = AirPassengersDataset().load().astype("float32")

batch_size = 3

model = TFTModel(
    input_chunk_length=12,
    output_chunk_length=6,
    add_relative_index=True,
    batch_size=batch_size,
    n_epochs=1,
)

# all batches in training set have length `3` (since we drop the last)
model.fit([series], dataloader_kwargs={"drop_last": True})
assert get_attn_shape(model)[0] == batch_size
# prints (3, 6, 4, 18)

# during prediction, the "full" batches have length min(len(series), batch_size) 
# (the last batch size is the number of leftover series in the last batch)
explainer = TFTExplainer(model, background_series=[series] * 1)
explanation = explainer.explain()
assert get_attn_shape(model)[0] == 1
# prints (1, 6, 4, 18)

# if you supply more series than the batch size, it will raise an index error
explanation = explainer.explain(foreground_series=[series] * (batch_size + 1))
```

</details>

I can add it to our backlog to raise an error when the number of series exceeds the batch size.

In the meantime, you can either:

- manually update the model's batch size with `model.batch_size = len(list_of_series)` (if it fits into memory)
- run `explain()` iteratively with `foreground_series` chunks of length `batch_size`

### Comment 2 ([user]):

Thanks [user] - that's a very helpful explanation. Makes a lot of sense, and good to know I wasn't completely losing my marbles... I'll make fixes at my end and look fwd to throwing an error in future (!). Great work on the library btw

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
