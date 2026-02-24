# TeamBench: Heterogeneous Teamwork Bench

> A multi-domain benchmark for evaluating teamwork among heterogeneous LLM agents.

Tasks are designed such that **no single agent** can simultaneously access:
1. The **full specification** (information partition)
2. **Write permissions** to the working environment (permission partition)
3. **Independent verification** + submission authority (verification independence)

This is enforced at the **OS level** via Docker containers and mount permissions — not by prompts.

## Why Teamwork Is Necessary (Objective Proof)

| Constraint | Mechanism | Bypass-proof? |
|---|---|---|
| **Information Partition** | Planner sees `spec.md`; Executor sees only `brief.md` | Yes — files not mounted |
| **Permission Partition** | Executor can write workspace; Planner/Verifier cannot | Yes — read-only mounts |
| **Verification Independence** | Only Verifier can write `attestation.json`; no attestation = auto-fail | Yes — mount policy |

### Teamwork Necessity Index (TNI)

```
TNI = (S_team - S_restricted) / max(epsilon, S_full - S_restricted)
```

- `S_full`: Single-agent with full access (oracle upper bound)
- `S_restricted`: Single-agent under TeamBench constraints
- `S_team`: Multi-agent team performance

TNI ~ 1.0 means teamwork fully recovers the performance gap.

## Roles

| Role | Can Read | Can Write | Can Execute |
|---|---|---|---|
| **Planner** | `spec.md`, `brief.md`, messages | messages | No |
| **Executor** | `brief.md`, workspace, reports, messages | workspace, reports | Yes |
| **Verifier** | `spec.md`, workspace (RO), reports (RO), messages | messages, submission | No |

## Task Domains (MVP: 3 tasks, target: 40+)

| Domain | Tasks | Artifact Type |
|---|---|---|
| Software Maintenance | S1 (Hidden Spec) | patch + tests |
| Ops/Incident Response | O1 (Service Health) | service health |
| Information Retrieval | IR2 (Misinfo Trap) | answer + evidence |
| Data/ETL (planned) | D1, D2 | parquet + schema |
| Policy Compliance (planned) | P1, P2 | config + compliance |
| Long-Horizon (planned) | LH1, LH2 | workflow state |

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### 1. Build images

```bash
docker compose build
```

### 2. Run a task

```bash
python -m harness.run_task --task S1_hidden_spec
```

### 3. Interact with role containers

```bash
docker exec -it teambench_planner bash    # Read spec, plan strategy
docker exec -it teambench_executor bash   # Execute fixes
docker exec -it teambench_verifier bash   # Verify & create attestation
```

### 4. Grade

```bash
python -m harness.grade_task --task S1_hidden_spec --run_dir shared/runs/<run_id>
```

### 5. Tear down

```bash
docker compose down
```

## Scoring

Each task produces `score.json`:

```json
{
  "pass": true,
  "primary": {"success": 1},
  "secondary": {
    "runtime_sec": 312,
    "messages": 18,
    "tokens": 8421
  },
  "failure_modes": []
}
```

**Hard rule**: Missing `attestation.json` = automatic FAIL.

## Agent Driver Interface

Any LLM can be plugged in by implementing `ModelAdapter`:

```python
from harness.agent_interface import ModelAdapter

class MyModelAdapter(ModelAdapter):
    def generate(self, messages: list[dict], **kwargs) -> str:
        # Call your LLM API here
        ...
```

See `harness/agent_interface.py` for role configs (`make_planner_config`, `make_executor_config`, `make_verifier_config`).

## Cross-Model Compatibility Matrix

Fix roles (P/E/V), vary model assignments:

```
C[i,j,k] = success_rate(Planner=Mi, Executor=Mj, Verifier=Mk)
```

Pre-registered hypotheses:
- **Cross-family synergy**: Mixed teams (Gemini+Claude+GPT) outperform homogeneous?
- **Role specialization**: Some models excel as Planner vs. Verifier?
- **Weak-link dominance**: Team performance bounded by min(role ability)?
- **Asymmetry**: Swapping model roles changes performance?

## Metrics

| Metric | Description |
|---|---|
| Success Rate | Task pass ratio |
| Pass^k | Stability across k seeded runs |
| Communication Cost | Messages / tokens / rounds |
| Execution Cost | Commands / runtime / budget used |
| Verifier Value | Hidden-violation catch rate |
| TNI | Teamwork necessity quantification |

## Failure Mode Taxonomy

| Code | Description |
|---|---|
| FM1 | Spec Omission (brief-only, missed requirements) |
| FM2 | Overfit to Visible Tests (hidden test failure) |
| FM3 | Execution Loop (retry without progress) |
| FM4 | Unsafe Change (policy/security violation) |
| FM5 | Evidence Hallucination (IR domain) |
| FM6 | Poor Repair (failed recovery) |
| FM7 | Verification Failure (verifier approved bad output) |

## Adding New Tasks

Create a folder in `tasks/` with:

```
tasks/MY_TASK/
  task.yaml      # Metadata (domain, time limit, seeds)
  spec.md        # Full specification (Planner/Verifier only)
  brief.md       # Summary (Executor only)
  setup.sh       # Workspace preparation
  grade.sh       # Deterministic grader -> score.json
  workspace/     # Initial code/data snapshot
  hidden/        # Grader-only test data (never mounted)
  corpus/        # Offline documents (if applicable)
```

## Repository Structure

```
teambench/
  docker-compose.yml          # 3-container sandbox (P/E/V)
  images/
    planner/Dockerfile
    executor/Dockerfile
    verifier/Dockerfile
  harness/
    run_task.py               # Task launcher
    grade_task.py              # Task grader
    agent_interface.py         # Standard LLM adapter interface
    schemas.py                 # Message/attestation/score schemas
    utils.py                   # Shared utilities
  tasks/
    S1_hidden_spec/            # Software: hidden spec trap
    O1_service_health/         # Ops: service recovery
    IR2_misinformation_trap/   # IR: misinfo + evidence
  leaderboard/
    schema.json                # Submission format
    aggregate.py               # TNI / pass^k / compatibility matrix
```

## License

Apache 2.0
