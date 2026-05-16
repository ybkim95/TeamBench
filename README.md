# TeamBench

A benchmark for evaluating multi-agent LLM coordination under **OS-enforced** Planner / Executor / Verifier role separation.

[![arXiv](https://img.shields.io/badge/arXiv-2605.07073-b31b1b)](https://arxiv.org/abs/2605.07073)
[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-ybkim95%2Fteambench-yellow)](https://huggingface.co/datasets/ybkim95/teambench)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Website](https://img.shields.io/badge/site-teambench.github.io-blue)](https://teambench.github.io)

TeamBench measures the marginal contribution of each role in an LLM agent team. Roles run in separate Docker containers with disjoint filesystem mounts: the Planner reads the full spec but cannot edit, the Executor edits the workspace but cannot read the full spec, and the Verifier reads the spec and the read-only workspace but cannot modify either. Every task ships a deterministic shell-script grader.

**931 evaluation instances · 19 categories · 5 ablation conditions · 27-configuration cross-provider grid · MIT-licensed.**

---

## Install

```bash
git clone https://github.com/ybkim95/TeamBench.git
cd TeamBench
pip install -e ".[all]"           # add provider SDKs (anthropic, openai, google-genai)
docker compose build              # OS-enforced role separation requires Docker
```

Set the providers you want to evaluate:

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
```

---

## Run an evaluation

A single task, one model, all 5 ablation conditions, seed 0:

```bash
python -m harness.ablation \
    --model gemini-3-flash-preview \
    --tasks DIST1_queue_race \
    --seeds 0 \
    --conditions oracle restricted full team_no_plan team_no_verify \
    --output shared/runs/example
```

The output writes one `score.json` per (task, condition) under `shared/runs/example/`. Each file contains `passed: true|false` and a partial score in `[0, 1]` from the deterministic grader.

The full TeamBench-90 leaderboard sweep (all 5 conditions across the 90 stratified tasks):

```bash
python -m harness.ablation \
    --model <your-model> \
    --tasks $(jq -r '.tasks[].task_id' leaderboard/data/leaderboard_90_tasks.json) \
    --seeds 0 \
    --conditions oracle restricted full team_no_plan team_no_verify \
    --output shared/ablation_results/lb90_<your-model>_seed0.json
```

The 90 task IDs are listed under the `tasks[].task_id` keys of `leaderboard/data/leaderboard_90_tasks.json` (a JSON object, not an array; `jq -r '.tasks[].task_id'` extracts them).

Aggregate scores and compute TNI:

```bash
python -m harness.compute_tni \
    --ablation shared/ablation_results/lb90_<model>_seed0.json \
    --output shared/ablation_results/tni_<model>.json

python -m harness.paper_tables \
    --ablation shared/ablation_results/lb90_<model>_seed0.json \
    --output-dir shared/paper/
```

---

## Try the harness without API keys

`--model mock` runs a deterministic stub that exercises the grading + sandboxing pipeline without calling any provider. Useful for CI and for sanity-checking new tasks:

```bash
python -m harness.ablation \
    --model mock \
    --tasks DIST1_queue_race \
    --seeds 0 \
    --conditions oracle \
    --output /tmp/mock_run
```

---

## Add your own model

Models route by prefix; bring your own by implementing `ToolCallAdapter`:

```python
from harness.agent_interface import ToolCallAdapter, AdapterResponse

class MyAdapter(ToolCallAdapter):
    def generate_with_tools(self, messages, system_prompt, tools) -> AdapterResponse:
        ...  # call your model, return text + tool_calls

    def get_usage(self) -> dict:
        return {"input_tokens": ..., "output_tokens": ..., "total_tokens": ...}
```

Any OpenAI-compatible endpoint (vLLM, Ollama, Together AI, ...) works through the OpenAI adapter via `--base-url`.

---

## Add your own task

```
tasks/<TASK_ID>/
├── spec.md       # Full requirements (Planner-only)
├── brief.md      # User-facing symptom (Executor)
├── workspace/    # Initial files
└── grade.sh      # Deterministic grader, exits non-zero on failure
```

Optional `generators/gen_<task_id>.py` parameterizes the workspace from a seed (so seeds 5+ can be held out for the leaderboard refresh).

Smoke test the task:

```bash
python -m harness.ablation \
    --model mock --tasks <TASK_ID> --seeds 0 1 2 \
    --conditions oracle full --output /tmp/smoke_<TASK_ID>
```

---

## Submit to the leaderboard

1. Run the full sweep across the 5 conditions on the 90 leaderboard tasks (`leaderboard/data/leaderboard_90_tasks.json`).
2. Open a PR adding `shared/ablation_results/lb90_<your-model>_seed0.json`.
3. Maintainers manually re-run the deterministic graders to verify the submission before adding the model to the leaderboard; the leaderboard only ranks verified submissions.

---

## License

MIT (see [LICENSE](LICENSE)). Tasks adapted from public GitHub issue trackers and UCI datasets retain their respective upstream licenses.
