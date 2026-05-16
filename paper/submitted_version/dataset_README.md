---
license: mit
pretty_name: TeamBench
size_categories:
  - n<1K
task_categories:
  - text-generation
tags:
  - multi-agent
  - benchmark
  - software-engineering
  - teamwork
  - evaluation
  - llm-evaluation
  - agent-coordination
  - role-separation
  - planner-executor-verifier
  - tni
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/train.json
      - split: test
        path: data/test.json
dataset_info:
  features:
    - name: task_id
      dtype: string
    - name: title
      dtype: string
    - name: category
      dtype: string
    - name: difficulty
      dtype: string
    - name: has_generator
      dtype: bool
    - name: ablation_scores
      dtype: string
    - name: tni
      dtype: float32
    - name: classification
      dtype: string
  splits:
    - name: train
      num_examples: 153
    - name: test
      num_examples: 120
---

# TeamBench: A Multi-Agent Teamwork Benchmark with OS-Enforced Role Separation

[![Paper](https://img.shields.io/badge/NeurIPS-2026%20D%26B-blue)](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
[![GitHub](https://img.shields.io/badge/GitHub-ybkim95%2FTeamBench-black)](https://github.com/ybkim95/TeamBench)
[![License](https://img.shields.io/badge/License-MIT-green)](https://choosealicense.com/licenses/mit/)
[![Croissant](https://img.shields.io/badge/Croissant-1.0-orange)](https://huggingface.co/datasets/ybkim95/teambench/resolve/main/croissant.json)

## Overview

**TeamBench** is a benchmark of **851 task templates** that expand to **931 seeded evaluation instances** across **19 base categories**. It evaluates whether LLM-based agent **teams** outperform a single oracle agent under **OS-enforced role separation** (Planner / Executor / Verifier in isolated sandboxes with distinct tool allow-lists), and reports the **Teamwork Necessity Index (TNI)**: a paired metric that quantifies how much a task requires coordinated multi-agent effort beyond what a capable single agent achieves alone.

The release includes deterministic shell-script graders, parameterized seeded workspace generators, full reference ablation data on a 153-task core, role-mixing studies, and a 40-session human pilot under matched role separation.

## Dataset Files

| File | Rows | Description |
|---|---|---|
| `teambench_dataset.json` | 931 | Canonical full release: every seeded instance with `task_id`, `title`, `category`, `difficulty`, `has_generator`, `ablation_scores` (when available; columns `oracle`/`restricted`/`team`/`team_no_plan`/`team_no_verify`), `tni` (= `(S_team − S_restricted) / max(0.05, S_solo − S_restricted)`; null when the necessity gap is below 0.05), and `classification` (`HIGH-TNI`/`TEAM-HELPS`/`NEUTRAL`/`TEAM-HURTS`). |
| `data/train.json` | 153 | Originally-authored core templates with complete 5-condition reference ablation data (used in capability analysis, Section 5 of the paper). |
| `data/test.json` | 120 | Hard subset for stratified leaderboard evaluation. |
| `croissant.json` | -- | NeurIPS 2026 dataset metadata (Croissant 1.0 + RAI). |

## Quickstart

```python
import json, urllib.request

URL = "https://huggingface.co/datasets/ybkim95/teambench/resolve/main/teambench_dataset.json"
with urllib.request.urlopen(URL) as r:
    tasks = json.load(r)

print(f"{len(tasks)} instances")
print(tasks[0])
```

Or via the `datasets` library:

```python
from datasets import load_dataset
ds = load_dataset("ybkim95/teambench")
print(ds)
```

The full task definitions (briefs, full specifications, generators, graders, sandbox configs) live in the GitHub repository: <https://github.com/ybkim95/TeamBench>. This Hugging Face mirror provides the structured metadata layer suitable for programmatic indexing.

## Task Origin Mix

| Origin | Templates | Description |
|---|---|---|
| Originally authored | 161 | Critical constraints placed exclusively in the full specification (absent from the brief and the workspace), so a single agent cannot solve the task without the Planner. |
| GitHub bug reports | 650 | Adapted from active open-source repositories (Flask, Click, httpx, Requests, Pydantic, Django, pytest, FastAPI, SQLAlchemy, Celery, Werkzeug, NumPy, SciPy, Keras, spaCy, etc.). Issue text and user-facing symptom go into the brief; the upstream fix patch becomes the deterministic grader. |
| UCI data-science | 30 | Canonical UCI public datasets (cited in the paper). |
| Public post-mortems | 10 | Adapted from public incident-response post-mortems. |
| **Total** | **851** | Each template has a parameterized generator that emits byte-identical workspaces from a fixed integer seed; held-out seeds are reserved for periodic leaderboard refresh. |

## Domain Distribution (Top Categories)

| Category | Tasks | Coordination signal |
|---|---|---|
| GitHub-derived (`Other`) | 733 | Library maintenance bug fixes |
| Security | 32 | Vulnerability patching, audit triage |
| Software Engineering | 31 | Hidden specs, backward compatibility |
| Incident Response | 26 | Cascade failure, memory leak, rollback |
| Operations | 17 | Container debugging, monitoring |
| Data Engineering | 15 | Schema drift, ETL repair |
| Testing | 12 | Spec-to-tests, mutation resistance |
| Policy | 9 | Access control, license compliance |
| Information Retrieval | 8 | Evidence QA, misinformation traps |
| Distributed Systems | 7 | Race conditions, Raft consensus |
| Adversarial | 7 | Spec conflicts, false bug reports, security theater |
| Code Review | 6 | API review, style enforcement |
| Multi-language | 6 | Go concurrency, JavaScript XSS |
| Long-Horizon | 6 | Multi-step migrations, staged deployments |
| Pipeline | 6 | API gateway, message queues |
| Cross-System Integration | 5 | API contract mismatches, schema evolution, auth federation |
| Specification | 3 | Feature implementation from RFC |
| Integration / Negotiation | 2 | Pipeline repair, trade-off configuration |

## Five-Condition Ablation

Each core task is evaluated under five conditions. The paper and website use the human-readable names (Solo, Restricted, Full Team, etc.); this dataset and the `harness` CLI store the machine names (`oracle`, `restricted`, etc.). The mapping is:

| Paper / Website name | Dataset / CLI key | Roles | Purpose |
|---|---|---|---|
| Solo               | `oracle`         | Single agent, full tool access      | Capability ceiling |
| Restricted         | `restricted`     | Single agent, executor-only tools   | Capability floor |
| Full Team          | `team`           | Planner + Executor + Verifier       | Full team |
| Team, No Plan      | `team_no_plan`   | Executor + Verifier                 | Isolates planner contribution |
| Team, No Evaluate  | `team_no_verify` | Planner + Executor                  | Isolates verifier contribution |

Scores are in `[0, 1]` (fraction of grader checks passed).

Ablation columns are populated for the 153 originally-authored core templates and the 120-task hard leaderboard subset. GitHub-derived rows ship with `ablation_scores: null` because they are scored against upstream patches rather than the 5-condition pipeline.

## TNI Metric

The Teamwork Necessity Index measures how much of the Solo-versus-Restricted gap the team recovers:

```
TNI = (S_team − S_restricted) / max(ε, S_solo − S_restricted),   ε = 0.05
```

`S_solo` is the `oracle` column in this dataset. The denominator is the "necessity gap": when Solo barely beats Restricted, TNI is unstable, so we only report it when the gap exceeds `ε`. `TNI = 1` recovers the full single-agent advantage; `TNI > 1` exceeds it. This matches Equation 1 of the paper.

Classification bands (from `harness/compute_tni.py`):

| Band | Rule | Interpretation |
|---|---|---|
| `HIGH-TNI`   | necessity gap > 0.1 and TNI > 0.2 | Coordination is necessary and the team recovers a substantial fraction of the necessity gap |
| `TEAM-HELPS` | team uplift > +0.05 (vs Restricted)  | Team helps |
| `NEUTRAL`    | absolute(team uplift) <= 0.05         | No clear team effect |
| `TEAM-HURTS` | team uplift < −0.05 (vs Restricted)   | Coordination overhead hurts |

where `team uplift = S_team − S_restricted`. Tasks with `ablation_scores: null` are unrated.

## Headline Findings

1. **Verifier false-accept rate of 49%** on grader-failing runs in the role-mixing pool, with removing the Verifier improving mean partial score in the reference ablation.
2. **Prompt-only and sandbox-enforced teams reach statistically indistinguishable pass rates**, but prompt-only runs produce **3.6 times more cases** where the Verifier rewrites the Executor's code.
3. **Conditional team value**: teams help most when single agents struggle (lowest Solo-score quintile, +15.7 points) but hurt on tasks where Solo already performs well.
4. **Human pilot** (40 sessions): Solo participants work through the task directly, Hybrid sessions often collapse into quick approval, and human teams spend more effort coordinating missing information across roles.

## Responsible-Use Note

Adversarial-trap (`TRAP*`) and security-vulnerability (`CRYPTO*`, `SEC*`) tasks contain **plausible-but-incorrect** security patterns by design (intentional nonce reuse, low PBKDF2 iterations, truncated authentication tags, etc.). These are synthetic evaluation cases and **must not be deployed**. Recommended use is in network-isolated containers, per the responsible-use note in the accompanying paper.

## Citation

```bibtex
@inproceedings{kim2026teambench,
  title     = {TeamBench: A Multi-Agent Teamwork Benchmark with OS-Enforced Role Separation},
  author    = {Kim, Yubin and Park, Chanwoo and Kim, Taehan and Park, Eugene and
               Schmidgall, Samuel and Rahman, Salman and Park, Chunjong and
               Breazeal, Cynthia and Liu, Xin and Palangi, Hamid and
               Park, Hae Won and McDuff, Daniel},
  booktitle = {NeurIPS 2026 Datasets and Benchmarks Track},
  year      = {2026}
}
```

## License

Released under the **MIT License**. Tasks adapted from public GitHub issue trackers and UCI datasets retain their respective upstream licenses; only the issue text and patch reference are used to construct deterministic graders.

## Links

- Paper (camera-ready): NeurIPS 2026 D&B (forthcoming)
- Code: <https://github.com/ybkim95/TeamBench>
- Croissant metadata: [`croissant.json`](https://huggingface.co/datasets/ybkim95/teambench/resolve/main/croissant.json)
- Issue tracker: <https://github.com/ybkim95/TeamBench/issues>
