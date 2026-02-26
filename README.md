# TeamBench: OS-Enforced Teamwork Benchmark for LLM Agents

> A multi-domain benchmark for evaluating whether LLM agents can collaborate effectively under OS-enforced role separation.

Unlike prior benchmarks that rely on prompt-based constraints, TeamBench uses **Docker containers with file-system mount policies** to enforce role boundaries. No single agent can simultaneously access the full specification, write to the workspace, and submit verification --- forcing genuine teamwork.

## Key Features

- **80 tasks** across **14 categories** with **251 seeded instances**
- **OS-level enforcement** via Docker bind mounts --- not prompt-based honor system
- **Contamination-resistant** parameterized generation (infinite seed variants per task)
- **8 programming languages**: Python, JavaScript, Go, SQL, Bash, JSON, Dockerfile, HTML
- **Model-agnostic** adapters for Gemini, GPT, Claude (and any OpenAI-compatible API)
- **5-condition ablation framework** with Teamwork Necessity Index (TNI)
- **Graded scoring** with partial credit and fine-grained failure mode taxonomy

## Why Teamwork Is Necessary

| Constraint | Mechanism | Bypass-proof? |
|---|---|---|
| **Information Partition** | Planner sees `spec.md`; Executor sees only `brief.md` | Yes --- file not mounted |
| **Permission Partition** | Executor can write workspace; Planner/Verifier cannot | Yes --- read-only mounts |
| **Verification Independence** | Only Verifier can write `attestation.json`; no attestation = auto-fail | Yes --- mount policy |

### Teamwork Necessity Index (TNI)

```
TNI = (S_team - S_restricted) / max(epsilon, S_oracle - S_restricted)
```

| Score | Interpretation |
|-------|---------------|
| ~1.0 | Teamwork fully recovers the performance gap |
| ~0.5 | Teamwork substantially helps |
| ~0.0 | Teamwork provides no benefit |
| < 0 | Teamwork is harmful |

## Roles

| Role | Can Read | Can Write | Can Execute |
|---|---|---|---|
| **Planner** | `spec.md`, `brief.md`, messages | messages only | No |
| **Executor** | `brief.md`, workspace, reports, messages | workspace, reports | Yes |
| **Verifier** | `spec.md`, workspace (RO), reports (RO), messages | submission (`attestation.json`) | No |

## Task Distribution (80 Tasks, 14 Categories)

| Category | Count | Difficulty Range | Example Tasks |
|---|---|---|---|
| Software Engineering | 10 | medium--expert | Hidden spec, dependency conflict, refactoring, backward compat |
| Data Engineering | 8 | medium--expert | Schema drift, data quality, pipeline repair, query optimization |
| Security | 8 | medium--expert | Vuln patch, auth bypass, crypto upgrade, CSRF, rate limiting |
| Incident Response | 7 | medium--expert | Cascade failure, data corruption, memory leak, deadlock |
| Long-Horizon | 7 | hard--expert | Multi-step pipeline, budgeted workflow, staged deploy, data migration |
| Operations | 6 | medium--expert | Service health, root cause, log analysis, container debug |
| Code Review | 5 | easy--hard | Review respond, style enforce, perf review, API review |
| Pipeline/Integration | 5 | medium--hard | ETL fix, API gateway, message queue, CI/CD |
| Policy/Compliance | 5 | medium--hard | Policy config, spec arbitration, access control, audit logging |
| Specification | 5 | medium--hard | Feature impl, API design, data model, config system |
| Information Retrieval | 4 | easy--hard | Evidence QA, misinformation trap, multi-source, temporal |
| Testing | 4 | medium--hard | Spec-to-tests, regression, integration, property-based |
| Multi-language | 3 | hard | Fullstack fix, API+frontend, polyglot |
| Negotiation | 3 | hard | Tradeoff config, cost-perf balance, tech debt |

**Difficulty distribution**: 49 hard, 19 medium, 10 expert, 2 easy

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (for container-based runs)

### Install

```bash
git clone https://github.com/ybkim95/TeamBench.git
cd TeamBench
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

### Run with LLM Agent (API key required)

```bash
# Set API keys
export GEMINI_API_KEY=...   # or OPENAI_API_KEY / ANTHROPIC_API_KEY

# Single task
python -m harness.run_agent --model gemini-2.5-flash --task P1_policy_config --seed 0

# Batch (all tasks, 3 seeds)
python -m harness.run_all --model gemini-2.5-flash --seeds 0 1 2

# Ablation study (5 conditions x selected tasks)
python -m harness.ablation --model gemini-2.5-flash --seeds 0 1 2

# Compute TNI from ablation results
python -m harness.compute_tni --ablation shared/ablation_results.json
```

### Run with Docker (OS-enforced role separation)

```bash
docker compose build
python -m harness.run_task --task S1_hidden_spec --seed 0

# Interact with role containers
docker exec -it teambench_planner bash    # Read spec, plan strategy
docker exec -it teambench_executor bash   # Execute fixes
docker exec -it teambench_verifier bash   # Verify & create attestation

# Grade
python -m harness.grade_task --task S1_hidden_spec --run_dir shared/runs/<run_id>

docker compose down
```

### Validate Infrastructure (no API keys needed)

```bash
# Run full validation
python -m harness.run_all --seeds 0  # Grades unmodified workspaces (all should fail)

# Generate benchmark statistics
python -m harness.benchmark_stats --json
python -m harness.benchmark_stats --latex
```

## Model Adapters

TeamBench supports any LLM via the `ToolCallAdapter` interface:

```python
from harness.agent_interface import ToolCallAdapter, AdapterResponse

class MyAdapter(ToolCallAdapter):
    def generate_with_tools(self, messages, system_prompt, tools) -> AdapterResponse:
        # Call your LLM API, return text + tool_calls
        ...
    def get_usage(self) -> dict:
        return {"input_tokens": ..., "output_tokens": ..., "total_tokens": ...}
```

Built-in adapters (auto-selected by model name prefix):

| Prefix | Adapter | Environment Variable |
|---|---|---|
| `gemini-*` | GeminiAdapter | `GEMINI_API_KEY` |
| `gpt-*`, `o1*`, `o3*` | OpenAIAdapter | `OPENAI_API_KEY` |
| `claude-*` | AnthropicAdapter | `ANTHROPIC_API_KEY` |
| `mock-*` | MockAdapter | (none --- for testing) |

## Contamination Resistance

Every task has a **parameterized generator** that produces unique instances per seed:

```python
from generators.registry import get_generator

gen = get_generator("P1_policy_config")

# Different seeds -> different data, different correct answers
r0 = gen.generate(seed=0)   # rate_limit=180, timeout=30, auth=jwt
r1 = gen.generate(seed=1)   # rate_limit=95, timeout=60, auth=saml
r42 = gen.generate(seed=42) # rate_limit=210, timeout=15, auth=oauth2

# Same seed -> deterministic
assert gen.generate(seed=0).expected == r0.expected
```

80 generators produce 251 instances (seeds [0,1,2]) with deterministic reproducibility.

## Ablation Framework

Five conditions to quantify the value of each architectural component:

| Condition | Description | What it measures |
|---|---|---|
| **Oracle** | Single agent, full access (spec + exec + verify) | Upper bound |
| **Restricted** | Single agent, executor-only (brief + exec) | Lower bound |
| **Team-NoPlan** | Executor + Verifier (no Planner) | Planning value |
| **Team-NoVerify** | Planner + Executor (no Verifier) | Verification value |
| **Full** | Planner + Executor + Verifier + remediation | Full team |

```bash
python -m harness.ablation --model gemini-2.5-flash --seeds 0 1 2

# Generate paper tables from ablation results
python -m harness.paper_tables --ablation shared/ablation_results.json --output-dir shared/paper/
```

## Scoring

Each task produces `score.json`:

```json
{
  "pass": true,
  "primary": {"success": 1},
  "secondary": {"partial_score": 0.85, "checks_passed": 6, "checks_total": 7},
  "failure_modes": ["hidden_spec_edge_case_x"]
}
```

**Hard rule**: Missing `attestation.json` = automatic FAIL (verifier must participate).

## Metrics

| Metric | Description |
|---|---|
| **Success Rate** | Binary pass/fail ratio |
| **Partial Score** | Fractional credit (0--1) for partial solutions |
| **Pass@k** | Stability: P(at least 1 pass in k seeded runs) |
| **TNI** | Teamwork Necessity Index (ablation-derived) |
| **Planning Value** | S_full - S_no_plan |
| **Verification Value** | S_full - S_no_verify |
| **Communication Cost** | Messages, tokens, rounds between agents |
| **Cross-Model Matrix** | C[planner_model, executor_model, verifier_model] |

## Failure Mode Taxonomy

| Code | Description |
|---|---|
| FM1 | Spec Omission --- Executor missed requirements only in spec |
| FM2 | Overfit to Visible --- Passed obvious checks, failed hidden ones |
| FM3 | Execution Loop --- Agent retried without making progress |
| FM4 | Unsafe Change --- Introduced security/policy violation |
| FM5 | Evidence Hallucination --- Cited non-existent evidence |
| FM6 | Poor Repair --- Failed remediation after verifier feedback |
| FM7 | Verification Failure --- Verifier approved incorrect output |

## Repository Structure

```
TeamBench/
  harness/
    run_agent.py             # Agent driver (model -> orchestrator -> grader)
    run_all.py               # Batch runner with setup_run/grade_run
    orchestrator.py          # 3-phase protocol: Plan -> Execute -> Verify
    agent_loop.py            # Single-agent tool-calling loop
    agent_interface.py       # ToolCallAdapter ABC, role configs, tools
    ablation.py              # 5-condition ablation framework + TNI
    compute_tni.py           # Per-task TNI computation and reporting
    paper_tables.py          # LaTeX table generation for paper
    benchmark_stats.py       # Task distribution analysis
    adapters/
      __init__.py            # create_adapter() factory
      openai_adapter.py      # GPT/O1/O3 adapter
      anthropic_adapter.py   # Claude adapter
      mock_adapter.py        # Deterministic mock for testing
    gemini_adapter.py        # Gemini adapter
  generators/
    base.py                  # TaskGenerator ABC, GeneratedTask dataclass
    primitives.py            # SeededRandom, NamePool, ValuePool
    registry.py              # Auto-discovery of gen_*.py generators
    gen_*.py                 # 80 parameterized generators (one per task)
  tasks/
    {TASK_ID}/
      task.yaml              # Metadata (domain, difficulty, languages, tags)
      spec.md                # Full specification (Planner + Verifier)
      brief.md               # Summary (Executor only)
      setup.sh               # Workspace preparation
      grade.sh               # Deterministic grader -> score.json
      workspace/             # Initial (buggy) code/data
      corpus/                # Offline documents (IR/policy tasks)
  leaderboard/
    schema.json              # Submission format
    aggregate.py             # Aggregation with dimensional breakdowns
  docker-compose.yml         # 3-container sandbox (P/E/V)
  images/{planner,executor,verifier}/Dockerfile
```

## Adding New Tasks

1. Create `generators/gen_my_task.py` implementing `TaskGenerator`
2. Create `tasks/MY_TASK/` with `task.yaml`, `spec.md`, `brief.md`, `setup.sh`, `grade.sh`, `workspace/`
3. Run `python -m harness.run_all --tasks MY_TASK --seeds 0` to validate the grader
4. Verify cross-seed diversity with `generators/registry.py`

## Pre-registered Hypotheses

1. **Teamwork is necessary**: TNI > 0.5 across most tasks (restricted baseline significantly underperforms)
2. **Planning value**: Removing the Planner significantly reduces partial scores
3. **Verification value**: Removing the Verifier significantly reduces pass rate
4. **Cross-family synergy**: Mixed teams (Gemini + Claude + GPT) outperform homogeneous teams
5. **Role specialization**: Some models excel as Planner vs. Executor vs. Verifier
6. **Difficulty calibration**: Expert tasks have < 20% pass rate; easy tasks have > 60%

## Citation

```bibtex
@article{teambench2026,
  title={TeamBench: OS-Enforced Teamwork Benchmark for Heterogeneous LLM Agent Teams},
  author={Kim, Youngbin and others},
  year={2026},
  note={https://github.com/ybkim95/TeamBench}
}
```

## License

Apache 2.0
