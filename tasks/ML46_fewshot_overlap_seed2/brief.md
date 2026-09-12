# ML46: Few-Shot Support/Query Overlap Bug (Brief)

## Your Task
Fix the episode sampler in `episode_sampler.py`.

Training a **episodic few-shot learner** shows unrealistically high training accuracy
but poor test performance — because the query set contains the same samples
as the support set.

## Symptoms
- Training accuracy near 100% even from epoch 1
- Test accuracy near random chance (0.33 for 3-way)
- Model does not generalize to genuinely unseen query examples

## What to Fix
- `episode_sampler.py`: `sample_episode()` — `query_idx` must start after `support_idx`
- Change `perm[:self.n_query]` to `perm[self.k_shot:self.k_shot + self.n_query]`
- Do NOT modify `train.py` or `model.py`

## Success Criteria
- `python check_fewshot.py` exits 0
- Test accuracy > 0.4
