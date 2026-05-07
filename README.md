# TeamBench

A multi-agent coordination benchmark with **OS-enforced** Planner / Executor / Verifier role separation.

[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-ybkim95%2Fteambench-yellow)](https://huggingface.co/datasets/ybkim95/teambench)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Website](https://img.shields.io/badge/site-teambench.github.io-blue)](https://teambench.github.io)

Most multi-agent benchmarks assign roles through prompts that any model can ignore. TeamBench enforces role boundaries with Docker bind mounts: the Planner reads the full spec but cannot edit, the Executor edits the workspace but cannot read the full spec, and the Verifier reads the spec and the read-only workspace but cannot modify either. Every task ships a deterministic shell-script grader.

**931 evaluation instances · 19 categories · 5 ablation conditions · 27-config cross-provider grid · MIT-licensed.**

---

## Install

```bash
git clone https://github.com/ybkim95/TeamBench.git
cd TeamBench
pip install -e .
```

Set the providers you want to use:

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
```

Docker is required for OS-enforced role separation:

```bash
docker compose build
```

---

## Run an evaluation

A single task, one model, all 5 ablation conditions, seed 0:

```bash
python -m harness.ablation \
    --task DIST1_queue_race \
    --model gemini-3-flash-preview \
    --seed 0 \
    --out shared/runs/example
```

The full 90-task leaderboard sweep:

```bash
python -m harness.run_all \
    --model gemini-3-flash-preview \
    --tasks-file leaderboard/data/leaderboard_100_tasks.json \
    --seeds 0 \
    --conditions oracle restricted team team_no_plan team_no_verify
```

Aggregate scores and compute TNI:

```bash
python -m harness.compute_tni  --runs-dir shared/runs/example
python -m harness.paper_tables --out shared/paper/
```

Each run writes `score.json` next to the trace, where the deterministic grader emits `passed: true|false` and a partial score in `[0,1]`.

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

Optional `generators/gen_<task_id>.py` parameterizes the workspace from a seed. Validate determinism and cross-seed uniqueness:

```bash
python -m harness.validate --task <TASK_ID> --seeds 0 1 2
```

---

## Submit to the leaderboard

1. Run the full sweep across the 5 conditions.
2. Open a PR adding `shared/leaderboard/leaderboard_<your-model>.json`.
3. Scores are server-side verified by re-running the deterministic graders; the leaderboard only ranks verified submissions.

---

## License

MIT (see [LICENSE](LICENSE)). Tasks adapted from public GitHub issue trackers and UCI datasets retain their respective upstream licenses.
