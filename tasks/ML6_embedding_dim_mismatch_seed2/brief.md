# ML6: Embedding Dimension Mismatch (Brief)

## Your Task
Fix `model.py` for **siamese network for similarity with projection mismatch** so the forward pass works.

Currently the model crashes immediately on any forward pass with:
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied
```

## What You Know
- Model code is in `model.py`
- There are **2 dimension mismatch bugs** in the layer definitions
- The Planner has the correct architecture diagram with exact dimensions
- After fixing, run `python check_model.py`

## Rules
- Fix only `model.py`
- Do not modify `check_model.py`
- Follow the Planner's architecture specification exactly
