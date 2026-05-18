"""TeamBench Leaderboard — Hugging Face Spaces app

Three tabs:
  - Leaderboard  (paper Table 4 / LB90, 13 models, 5 conditions)
  - Instructions (install, run an evaluation, compute TNI)
  - Submit       (model name + results JSON upload, written to submissions/)
"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path

import gradio as gr
import pandas as pd

ROOT = Path(__file__).parent
SUBMISSIONS_DIR = ROOT / "submissions"
SUBMISSIONS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# LB90 leaderboard from paper Table tab:lb90-leaderboard
# Pass-rate (%) per condition. Sort: max(Solo, Full) desc.
# ---------------------------------------------------------------------------
LEADERBOARD = [
    {"model": "Claude Opus 4.7",       "provider": "Anthropic", "Solo": 35.6, "Restricted": 33.3, "No Plan": 35.6, "No Eval": 33.3, "Full": 37.8},
    {"model": "GPT-5.4 Mini",          "provider": "OpenAI",    "Solo": 33.3, "Restricted": 23.3, "No Plan": 25.6, "No Eval": 24.4, "Full": 28.9},
    {"model": "Claude Haiku 4.5",      "provider": "Anthropic", "Solo": 12.2, "Restricted": 31.1, "No Plan": 18.9, "No Eval":  1.1, "Full": 28.9},
    {"model": "Gemini-3.1 Pro",        "provider": "Google",    "Solo": 27.8, "Restricted": 22.2, "No Plan": 16.7, "No Eval": 25.6, "Full": 28.9},
    {"model": "Claude Sonnet 4.6",     "provider": "Anthropic", "Solo":  7.8, "Restricted": 27.8, "No Plan": 10.0, "No Eval":  6.7, "Full": 27.8},
    {"model": "GPT-5.4",               "provider": "OpenAI",    "Solo": 12.2, "Restricted": 35.6, "No Plan": 23.3, "No Eval": 34.4, "Full": 27.8},
    {"model": "Gemma 4 31B",           "provider": "Google",    "Solo": 27.8, "Restricted": 25.6, "No Plan": 24.4, "No Eval": 20.0, "Full": 22.2},
    {"model": "Gemini-3 Flash",        "provider": "Google",    "Solo": 13.3, "Restricted": 18.9, "No Plan": 14.4, "No Eval": 27.8, "Full": 25.6},
    {"model": "Gemini-3.1 Flash Lite", "provider": "Google",    "Solo":  5.6, "Restricted": 21.1, "No Plan":  8.9, "No Eval": 17.8, "Full": 17.8},
    {"model": "gpt-oss-20b",           "provider": "OpenAI",    "Solo": 17.8, "Restricted": 17.8, "No Plan": 12.2, "No Eval":  7.8, "Full":  2.2},
    {"model": "Qwen 3 14B",            "provider": "Alibaba",   "Solo":  5.6, "Restricted":  2.2, "No Plan":  2.2, "No Eval":  1.1, "Full":  2.2},
    {"model": "Qwen 3 32B",            "provider": "Alibaba",   "Solo":  5.6, "Restricted":  3.3, "No Plan":  0.0, "No Eval":  5.6, "Full":  1.1},
    {"model": "Qwen 3 8B",             "provider": "Alibaba",   "Solo":  2.2, "Restricted":  5.6, "No Plan":  1.1, "No Eval":  3.3, "Full":  0.0},
]


def build_leaderboard_df():
    df = pd.DataFrame(LEADERBOARD)
    df.insert(0, "#", range(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# Submission validator
# ---------------------------------------------------------------------------
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")


def validate_submission(file_obj, model: str, team: str, contact: str, framework: str, description: str):
    if file_obj is None:
        return "**Error.** Please attach a JSON results file produced by `python -m harness.ablation`."
    if not model or not SAFE_NAME.match(model):
        return "**Error.** Model name is required and may only contain letters, digits, `.`, `_`, `-`."
    if not team:
        return "**Error.** Team / organization is required."

    src = Path(file_obj.name if hasattr(file_obj, "name") else file_obj)
    try:
        with open(src) as f:
            payload = json.load(f)
    except Exception as e:
        return f"**Error.** Could not parse JSON: `{e}`"

    if not isinstance(payload, (list, dict)):
        return "**Error.** Results JSON must be a list of run records or a `{tasks: [...], conditions: {...}}` object."

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_dir = SUBMISSIONS_DIR / f"{model}-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2))
    meta = {
        "submitted_at_utc": ts,
        "model": model,
        "team": team,
        "framework": framework or None,
        "contact": contact or None,
        "description": description or None,
        "filename": src.name,
        "n_records": len(payload) if isinstance(payload, list) else None,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return (
        f"**Submission received** at `submissions/{out_dir.name}/`. We manually re-run the "
        f"deterministic graders to verify your results before adding the model to the "
        f"leaderboard; turnaround is typically a few days. For status updates, "
        f"open an issue at https://github.com/ybkim95/TeamBench/issues."
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
CSS = """
.tb-hero { padding: 1.25rem 1.5rem; border-radius: 12px; background: linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 50%,#2563eb 100%); color: #fff; margin-bottom: 1rem; }
.tb-hero h1 { color: #fff !important; margin: 0 0 0.35rem; font-weight: 700; }
.tb-hero p  { color: rgba(255,255,255,0.95) !important; margin: 0; }
"""


def build_app():
    with gr.Blocks(css=CSS, title="TeamBench Leaderboard") as demo:
        gr.HTML(
            """
            <div class="tb-hero">
              <h1>TeamBench Leaderboard</h1>
              <p>Multi-agent LLM coordination on 90 stratified tasks under OS-enforced Planner / Executor / Verifier role separation. Five conditions per task, deterministic graders, MIT-licensed.</p>
            </div>
            """
        )

        with gr.Tabs():
            with gr.Tab("Leaderboard"):
                gr.Markdown(
                    "Pass rate (%) per condition on **TeamBench-90**. Models are sorted by `max(Solo, Full)`. "
                    "Source: paper main results (TeamBench-Verified covers 57 of these 90 tasks)."
                )
                gr.Dataframe(value=build_leaderboard_df(), interactive=False, wrap=False)
                gr.Markdown(
                    "**Five conditions** &nbsp; "
                    "`Solo` (one agent, full access) · "
                    "`Restricted` (one agent, executor tools only) · "
                    "`No Plan` (Executor + Verifier; Verifier holds the spec) · "
                    "`No Eval` (Planner + Executor) · "
                    "`Full` (Planner + Executor + Verifier)."
                )

            with gr.Tab("Instructions"):
                gr.Markdown(
                    """
### 1. Install

```bash
git clone https://github.com/ybkim95/TeamBench.git
cd TeamBench
pip install -e ".[all]"
docker compose build
```

Set the providers you want to evaluate:

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
```

### 2. Run a single task across all five conditions

```bash
python -m harness.ablation \\
    --model gemini-3-flash-preview \\
    --tasks DIST1_queue_race \\
    --seeds 0 \\
    --conditions oracle restricted full team_no_plan team_no_verify \\
    --output shared/runs/example
```

Each `score.json` under `shared/runs/example/<task>/<condition>/` contains `passed: true|false` and a partial score in `[0, 1]` from the deterministic shell-script grader. No API keys handy? `--model mock` runs an in-process stub that exercises the grader pipeline without provider calls.

### 3. Run the full TeamBench-90 sweep (all 5 conditions)

```bash
python -m harness.ablation \\
    --model <your-model> \\
    --tasks $(jq -r '.tasks[].task_id' leaderboard/data/leaderboard_90_tasks.json) \\
    --seeds 0 \\
    --conditions oracle restricted full team_no_plan team_no_verify \\
    --output shared/ablation_results/lb90_<your-model>_seed0.json
```

Note: `leaderboard_90_tasks.json` is a JSON object (keys: `version`, `n_tasks`, `tasks`, ...); use `jq -r '.tasks[].task_id'` to extract the 90 task IDs.

### 4. Compute TNI and the paper tables

```bash
python -m harness.compute_tni \\
    --ablation shared/ablation_results/lb90_<model>_seed0.json \\
    --output shared/ablation_results/tni_<model>.json

python -m harness.paper_tables \\
    --ablation shared/ablation_results/lb90_<model>_seed0.json \\
    --output-dir shared/paper/
```

### 5. Submit

Open a Pull Request on GitHub adding your `shared/ablation_results/lb90_<your-model>_seed0.json` file. A validation workflow checks schema and integrity automatically; a maintainer then manually re-runs the deterministic graders before merging, and the leaderboard data is regenerated on merge to `main`.
                    """
                )

            with gr.Tab("Submit"):
                gr.Markdown(
                    """
### How to submit

Submissions are accepted exclusively through GitHub Pull Requests. We previously
ran an upload form here, but Hugging Face Spaces use ephemeral storage and no
maintainer was polling the directory, so uploads were effectively lost. To avoid
that, we have switched to the GitHub flow:

1. Run the LB90 sweep locally and produce
   `shared/ablation_results/lb90_<your-model>_seed0.json`.
2. Open a Pull Request adding that file at the same path in the GitHub repo:
   <https://github.com/ybkim95/TeamBench/pulls>
3. The `Validate Leaderboard Submission` workflow runs automatically and
   comments the schema/integrity result on the PR.
4. A maintainer manually re-runs the deterministic graders against your
   submission before merging.
5. On merge, the `Update Leaderboard` workflow regenerates
   `leaderboard/data/leaderboard_data.json`; this Space picks up the new
   numbers on its next launch.

If you cannot open a PR directly (e.g. inside a corporate firewall), open an
issue at <https://github.com/ybkim95/TeamBench/issues> and attach the JSON
there; we will route it into a PR on your behalf.
                    """
                )

        gr.Markdown(
            "<div style='text-align:center;color:#9ca3af;font-size:0.78rem;margin-top:1.25rem;'>"
            "TeamBench &middot; <a href='https://github.com/ybkim95/TeamBench'>GitHub</a> &middot; "
            "<a href='https://huggingface.co/datasets/ybkim95/teambench'>HuggingFace</a> &middot; "
            "<a href='https://teambench.github.io'>teambench.github.io</a>"
            "</div>"
        )
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
