"""
Parameterized generator for NEG2: Cost vs Performance Optimization.

Each seed produces:
  - Different system type (web_tier, data_tier, cache_tier, compute_tier)
  - Different cost model (per-instance costs, storage, bandwidth)
  - Different performance targets (p50, p99, throughput)
  - Different budget constraint
  - Same optimization challenge: suboptimal config must be improved within budget
"""
from __future__ import annotations

import json

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# System type configurations — four distinct profiles
SYSTEM_CONFIGS = [
    {
        "system_type": "web_tier",
        "description": "stateless HTTP application servers behind a load balancer",
        # Cost model (per month)
        "instance_types": {
            "small":  {"vcpu": 2,  "ram_gb": 4,  "cost_per_month": 35.0},
            "medium": {"vcpu": 4,  "ram_gb": 8,  "cost_per_month": 70.0},
            "large":  {"vcpu": 8,  "ram_gb": 16, "cost_per_month": 140.0},
            "xlarge": {"vcpu": 16, "ram_gb": 32, "cost_per_month": 280.0},
        },
        "storage_cost_per_gb": 0.10,
        "bandwidth_cost_per_gb": 0.09,
        "base_storage_gb": 50,
        "base_bandwidth_gb": 200,
        # Performance targets
        "p50_target_ms": 50,
        "p99_target_ms": 200,
        "throughput_target_rps": 1000,
        "reliability_target": 0.999,
        # Budget
        "budget_per_month": 500,
        # Suboptimal starting config (wrong instance type + over-provisioned instances)
        "bad_config": {
            "instance_type": "large",
            "instance_count": 6,
            "cache_size_mb": 64,
            "thread_count": 2,
            "batch_size": 1,
            "connection_pool_size": 5,
            "enable_compression": False,
            "enable_keep_alive": False,
        },
        # One valid optimal config (used in expected)
        "optimal_config": {
            "instance_type": "medium",
            "instance_count": 4,
            "cache_size_mb": 512,
            "thread_count": 8,
            "batch_size": 50,
            "connection_pool_size": 20,
            "enable_compression": True,
            "enable_keep_alive": True,
        },
        # Score weights
        "weights": {"performance": 0.40, "cost": 0.30, "reliability": 0.30},
        # Simulator params (base latencies without config tuning)
        "base_p50_ms": 120,
        "base_p99_ms": 450,
        "base_throughput_rps": 300,
        "base_reliability": 0.95,
    },
    {
        "system_type": "data_tier",
        "description": "database cluster with read replicas and write primary",
        "instance_types": {
            "small":  {"vcpu": 2,  "ram_gb": 8,   "cost_per_month": 50.0},
            "medium": {"vcpu": 4,  "ram_gb": 16,  "cost_per_month": 100.0},
            "large":  {"vcpu": 8,  "ram_gb": 32,  "cost_per_month": 200.0},
            "xlarge": {"vcpu": 16, "ram_gb": 64,  "cost_per_month": 400.0},
        },
        "storage_cost_per_gb": 0.115,
        "bandwidth_cost_per_gb": 0.07,
        "base_storage_gb": 100,
        "base_bandwidth_gb": 150,
        "p50_target_ms": 30,
        "p99_target_ms": 150,
        "throughput_target_rps": 500,
        "reliability_target": 0.9999,
        "budget_per_month": 500,
        "bad_config": {
            "instance_type": "xlarge",
            "instance_count": 3,
            "cache_size_mb": 32,
            "thread_count": 1,
            "batch_size": 1,
            "connection_pool_size": 3,
            "enable_compression": False,
            "enable_keep_alive": False,
        },
        "optimal_config": {
            "instance_type": "medium",
            "instance_count": 3,
            "cache_size_mb": 2048,
            "thread_count": 16,
            "batch_size": 100,
            "connection_pool_size": 30,
            "enable_compression": True,
            "enable_keep_alive": True,
        },
        "weights": {"performance": 0.40, "cost": 0.30, "reliability": 0.30},
        "base_p50_ms": 80,
        "base_p99_ms": 350,
        "base_throughput_rps": 150,
        "base_reliability": 0.97,
    },
    {
        "system_type": "cache_tier",
        "description": "distributed in-memory cache cluster (Redis-compatible)",
        "instance_types": {
            "small":  {"vcpu": 2,  "ram_gb": 8,   "cost_per_month": 40.0},
            "medium": {"vcpu": 4,  "ram_gb": 16,  "cost_per_month": 80.0},
            "large":  {"vcpu": 8,  "ram_gb": 32,  "cost_per_month": 160.0},
            "xlarge": {"vcpu": 16, "ram_gb": 64,  "cost_per_month": 320.0},
        },
        "storage_cost_per_gb": 0.08,
        "bandwidth_cost_per_gb": 0.06,
        "base_storage_gb": 30,
        "base_bandwidth_gb": 500,
        "p50_target_ms": 5,
        "p99_target_ms": 25,
        "throughput_target_rps": 5000,
        "reliability_target": 0.9995,
        "budget_per_month": 500,
        "bad_config": {
            "instance_type": "large",
            "instance_count": 5,
            "cache_size_mb": 128,
            "thread_count": 1,
            "batch_size": 1,
            "connection_pool_size": 5,
            "enable_compression": False,
            "enable_keep_alive": False,
        },
        "optimal_config": {
            "instance_type": "medium",
            "instance_count": 4,
            "cache_size_mb": 8192,
            "thread_count": 4,
            "batch_size": 200,
            "connection_pool_size": 50,
            "enable_compression": False,
            "enable_keep_alive": True,
        },
        "weights": {"performance": 0.40, "cost": 0.30, "reliability": 0.30},
        "base_p50_ms": 15,
        "base_p99_ms": 80,
        "base_throughput_rps": 1200,
        "base_reliability": 0.99,
    },
    {
        "system_type": "compute_tier",
        "description": "batch processing workers for CPU-intensive jobs",
        "instance_types": {
            "small":  {"vcpu": 4,  "ram_gb": 8,   "cost_per_month": 60.0},
            "medium": {"vcpu": 8,  "ram_gb": 16,  "cost_per_month": 120.0},
            "large":  {"vcpu": 16, "ram_gb": 32,  "cost_per_month": 240.0},
            "xlarge": {"vcpu": 32, "ram_gb": 64,  "cost_per_month": 480.0},
        },
        "storage_cost_per_gb": 0.05,
        "bandwidth_cost_per_gb": 0.04,
        "base_storage_gb": 200,
        "base_bandwidth_gb": 100,
        "p50_target_ms": 200,
        "p99_target_ms": 800,
        "throughput_target_rps": 200,
        "reliability_target": 0.995,
        "budget_per_month": 500,
        "bad_config": {
            "instance_type": "small",
            "instance_count": 2,
            "cache_size_mb": 64,
            "thread_count": 1,
            "batch_size": 1,
            "connection_pool_size": 2,
            "enable_compression": False,
            "enable_keep_alive": False,
        },
        "optimal_config": {
            "instance_type": "medium",
            "instance_count": 3,
            "cache_size_mb": 1024,
            "thread_count": 16,
            "batch_size": 500,
            "connection_pool_size": 10,
            "enable_compression": True,
            "enable_keep_alive": True,
        },
        "weights": {"performance": 0.40, "cost": 0.30, "reliability": 0.30},
        "base_p50_ms": 500,
        "base_p99_ms": 2000,
        "base_throughput_rps": 60,
        "base_reliability": 0.98,
    },
]


def _compute_monthly_cost(cfg_dict: dict, sys_cfg: dict) -> float:
    """Compute monthly cost from a config dict and system config."""
    instance_type = cfg_dict.get("instance_type", "medium")
    instance_count = cfg_dict.get("instance_count", 1)
    instance_cost = sys_cfg["instance_types"][instance_type]["cost_per_month"]
    storage_gb = sys_cfg["base_storage_gb"]
    bandwidth_gb = sys_cfg["base_bandwidth_gb"]
    return (
        instance_cost * instance_count
        + storage_gb * sys_cfg["storage_cost_per_gb"]
        + bandwidth_gb * sys_cfg["bandwidth_cost_per_gb"]
    )


class Generator(TaskGenerator):
    task_id = "NEG2_cost_perf"
    domain = "operations"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        sys_cfg = SYSTEM_CONFIGS[seed % len(SYSTEM_CONFIGS)]

        bad_cost = _compute_monthly_cost(sys_cfg["bad_config"], sys_cfg)
        opt_cost = _compute_monthly_cost(sys_cfg["optimal_config"], sys_cfg)

        expected = {
            "system_type": sys_cfg["system_type"],
            "budget_per_month": sys_cfg["budget_per_month"],
            "p50_target_ms": sys_cfg["p50_target_ms"],
            "p99_target_ms": sys_cfg["p99_target_ms"],
            "throughput_target_rps": sys_cfg["throughput_target_rps"],
            "reliability_target": sys_cfg["reliability_target"],
            "bad_config_cost": round(bad_cost, 2),
            "example_optimal_cost": round(opt_cost, 2),
            "constraints": {
                "cost_within_budget": True,
                "p50_meets_target": True,
                "p99_meets_target": True,
                "throughput_meets_target": True,
                "reliability_above_threshold": True,
                "weighted_score_above_baseline": True,
            },
        }

        workspace_files = self._build_workspace(sys_cfg, rng)
        spec_md = self._generate_spec(sys_cfg)
        brief_md = self._generate_brief(sys_cfg)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ------------------------------------------------------------------
    # Workspace builder
    # ------------------------------------------------------------------
    def _build_workspace(self, sys_cfg: dict, rng: SeededRandom) -> dict[str, str]:
        files: dict[str, str] = {}

        bad = sys_cfg["bad_config"]
        instance_types_json = json.dumps(sys_cfg["instance_types"], indent=2)

        # config.json — the suboptimal starting config agents must improve
        files["config.json"] = json.dumps({
            "system_type": sys_cfg["system_type"],
            "instance_type": bad["instance_type"],
            "instance_count": bad["instance_count"],
            "cache_size_mb": bad["cache_size_mb"],
            "thread_count": bad["thread_count"],
            "batch_size": bad["batch_size"],
            "connection_pool_size": bad["connection_pool_size"],
            "enable_compression": bad["enable_compression"],
            "enable_keep_alive": bad["enable_keep_alive"],
        }, indent=2) + "\n"

        # simulator.py — deterministic cost/perf simulator
        p50_t = sys_cfg["p50_target_ms"]
        p99_t = sys_cfg["p99_target_ms"]
        tput_t = sys_cfg["throughput_target_rps"]
        rel_t = sys_cfg["reliability_target"]
        budget = sys_cfg["budget_per_month"]
        stor_cost = sys_cfg["storage_cost_per_gb"]
        bw_cost = sys_cfg["bandwidth_cost_per_gb"]
        base_stor = sys_cfg["base_storage_gb"]
        base_bw = sys_cfg["base_bandwidth_gb"]
        base_p50 = sys_cfg["base_p50_ms"]
        base_p99 = sys_cfg["base_p99_ms"]
        base_tput = sys_cfg["base_throughput_rps"]
        base_rel = sys_cfg["base_reliability"]
        weights = sys_cfg["weights"]

        files["simulator.py"] = f'''"""
Cost/Performance simulator for {sys_cfg["system_type"]}.

Usage:
    python simulator.py                     # evaluate config.json
    python simulator.py --config my.json    # evaluate a custom config file
    python simulator.py --check             # exit 0 if all targets met, else 1

The simulator models how configuration knobs affect:
  - Monthly cost (instance + storage + bandwidth)
  - p50 / p99 latency (ms)
  - Throughput (requests per second)
  - Reliability (0-1 fraction of successful requests)
  - Weighted score (40% performance, 30% cost, 30% reliability)

Edit config.json to change the configuration, then re-run.
"""
import argparse
import json
import math
import sys


# ── Instance catalogue ────────────────────────────────────────────────────────
INSTANCE_TYPES = {instance_types_json}

STORAGE_COST_PER_GB   = {stor_cost}   # $/GB/month
BANDWIDTH_COST_PER_GB = {bw_cost}  # $/GB/month
BASE_STORAGE_GB       = {base_stor}
BASE_BANDWIDTH_GB     = {base_bw}
BUDGET_PER_MONTH      = {budget}   # hard cap

# ── Performance targets ───────────────────────────────────────────────────────
P50_TARGET_MS         = {p50_t}    # p50 latency must be below this
P99_TARGET_MS         = {p99_t}    # p99 latency must be below this
THROUGHPUT_TARGET_RPS = {tput_t}   # minimum requests per second
RELIABILITY_TARGET    = {rel_t}    # minimum success rate (0-1)

# ── Scoring weights ───────────────────────────────────────────────────────────
WEIGHT_PERFORMANCE = {weights["performance"]}
WEIGHT_COST        = {weights["cost"]}
WEIGHT_RELIABILITY = {weights["reliability"]}

# ── Baseline (worst acceptable) for score normalisation ──────────────────────
# These match the suboptimal config shipped in config.json.
BASELINE_P50_MS    = {base_p50}
BASELINE_P99_MS    = {base_p99}
BASELINE_TPUT_RPS  = {base_tput}
BASELINE_REL       = {base_rel}


# ─────────────────────────────────────────────────────────────────────────────
# Cost model
# ─────────────────────────────────────────────────────────────────────────────

def compute_cost(cfg: dict) -> float:
    """Compute estimated monthly cost in USD."""
    itype = cfg.get("instance_type", "medium")
    count = cfg.get("instance_count", 1)
    if itype not in INSTANCE_TYPES:
        raise ValueError(f"Unknown instance_type: {{itype!r}}. "
                         f"Valid options: {{list(INSTANCE_TYPES)}}")
    instance_cost = INSTANCE_TYPES[itype]["cost_per_month"] * count
    storage_cost  = BASE_STORAGE_GB   * STORAGE_COST_PER_GB
    bandwidth_cost = BASE_BANDWIDTH_GB * BANDWIDTH_COST_PER_GB
    return instance_cost + storage_cost + bandwidth_cost


# ─────────────────────────────────────────────────────────────────────────────
# Performance model
# ─────────────────────────────────────────────────────────────────────────────

def compute_performance(cfg: dict) -> dict:
    """
    Compute estimated performance metrics.

    The model encodes realistic relationships between knobs and metrics:

    Latency is reduced by:
      - More/larger instances  (horizontal + vertical scaling)
      - Larger cache           (cache hit rate improvement)
      - More threads           (concurrency)
      - keep-alive enabled     (connection reuse, -15% p50)
      - compression enabled    (reduces bandwidth but adds CPU, net -5% p99)

    Throughput is increased by:
      - More instances
      - More threads
      - Larger batch size      (amortises per-request overhead)
      - Larger connection pool

    Reliability is improved by:
      - More instances         (redundancy)
      - keep-alive             (avoids reconnect storms)
      - Larger cache           (fewer backend calls = fewer failure points)
    """
    itype   = cfg.get("instance_type", "medium")
    count   = cfg.get("instance_count", 1)
    cache   = cfg.get("cache_size_mb", 64)
    threads = cfg.get("thread_count", 1)
    batch   = cfg.get("batch_size", 1)
    pool    = cfg.get("connection_pool_size", 5)
    compress = cfg.get("enable_compression", False)
    keepalive = cfg.get("enable_keep_alive", False)

    if itype not in INSTANCE_TYPES:
        raise ValueError(f"Unknown instance_type: {{itype!r}}")

    spec = INSTANCE_TYPES[itype]
    vcpu = spec["vcpu"]

    # ── Latency model ─────────────────────────────────────────────────────────
    # Start from baseline; apply multiplicative reductions
    p50 = BASELINE_P50_MS
    p99 = BASELINE_P99_MS

    # Vertical scaling: vcpu multiplier (log scale, diminishing returns)
    vcpu_factor = 1.0 / math.log2(vcpu + 1)
    p50 *= vcpu_factor
    p99 *= vcpu_factor

    # Horizontal scaling: more instances share load
    count_factor = 1.0 / math.sqrt(count)
    p50 *= count_factor
    p99 *= count_factor

    # Cache: larger cache reduces backend round-trips (log scale)
    cache_factor = 1.0 / (1 + 0.12 * math.log2(max(cache, 1) + 1))
    p50 *= cache_factor
    p99 *= cache_factor

    # Thread count: parallelism reduces queuing latency
    thread_factor = 1.0 / math.log2(threads + 2)
    p50 *= thread_factor
    p99 *= thread_factor

    # Keep-alive: avoids handshake overhead
    if keepalive:
        p50 *= 0.85
        p99 *= 0.88

    # Compression: slightly increases CPU but reduces network RTT
    if compress:
        p50 *= 0.97
        p99 *= 0.95

    # ── Throughput model ──────────────────────────────────────────────────────
    tput = BASELINE_TPUT_RPS

    # Instance scaling
    tput *= count * math.log2(vcpu + 1)

    # Thread and pool scaling
    tput *= math.log2(threads + 2) * math.log2(pool + 2) / 4.0

    # Batch amortisation (log scale)
    tput *= (1 + 0.08 * math.log2(max(batch, 1) + 1))

    if keepalive:
        tput *= 1.20

    # ── Reliability model ─────────────────────────────────────────────────────
    # Baseline failure rate improves with redundancy + cache
    failure_rate = 1.0 - BASELINE_REL

    # More instances = less single-point-of-failure impact
    failure_rate /= math.sqrt(count)

    # Larger cache reduces backend dependency
    failure_rate /= (1 + 0.05 * math.log2(max(cache, 1) + 1))

    # Keep-alive avoids reconnect cascades
    if keepalive:
        failure_rate *= 0.70

    reliability = max(0.0, min(1.0, 1.0 - failure_rate))

    return {{
        "p50_ms": round(p50, 1),
        "p99_ms": round(p99, 1),
        "throughput_rps": round(tput, 1),
        "reliability": round(reliability, 6),
    }}


# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────

def score_performance(perf: dict) -> float:
    """
    Performance sub-score in [0, 1].

    Measures how far below the targets each metric sits.
    A score of 1.0 means all targets are perfectly met.
    Missing any target hard-caps the sub-score below 0.5.
    """
    p50_ok   = perf["p50_ms"]        <= P50_TARGET_MS
    p99_ok   = perf["p99_ms"]        <= P99_TARGET_MS
    tput_ok  = perf["throughput_rps"] >= THROUGHPUT_TARGET_RPS

    # Fractional contribution from each dimension
    p50_score  = min(1.0, P50_TARGET_MS / max(perf["p50_ms"], 1))
    p99_score  = min(1.0, P99_TARGET_MS / max(perf["p99_ms"], 1))
    tput_score = min(1.0, perf["throughput_rps"] / THROUGHPUT_TARGET_RPS)

    raw = (p50_score + p99_score + tput_score) / 3.0

    # Penalty for missing hard targets
    if not (p50_ok and p99_ok and tput_ok):
        raw *= 0.5

    return round(raw, 4)


def score_cost(cost: float) -> float:
    """
    Cost sub-score in [0, 1].

    Higher score = lower cost relative to budget.
    Exceeding the budget yields 0.
    """
    if cost > BUDGET_PER_MONTH:
        return 0.0
    # Linear: spending 0 = 1.0, spending exactly budget = 0.5
    utilisation = cost / BUDGET_PER_MONTH
    return round(1.0 - 0.5 * utilisation, 4)


def score_reliability(perf: dict) -> float:
    """Reliability sub-score in [0, 1]."""
    rel = perf["reliability"]
    if rel < RELIABILITY_TARGET:
        # Partial credit proportional to how close we are
        return round(rel / RELIABILITY_TARGET * 0.5, 4)
    # Above threshold: linear bonus for exceeding target (capped at 1.0)
    return round(min(1.0, 0.5 + (rel - RELIABILITY_TARGET) * 10), 4)


def weighted_score(cost: float, perf: dict) -> float:
    """Compute overall weighted score."""
    sp = score_performance(perf)
    sc = score_cost(cost)
    sr = score_reliability(perf)
    return round(
        WEIGHT_PERFORMANCE * sp +
        WEIGHT_COST        * sc +
        WEIGHT_RELIABILITY * sr,
        4,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Target checkers (used by grade.sh)
# ─────────────────────────────────────────────────────────────────────────────

def check_all(cfg: dict) -> dict:
    cost = compute_cost(cfg)
    perf = compute_performance(cfg)
    ws   = weighted_score(cost, perf)

    # Baseline score (suboptimal config)
    from copy import deepcopy
    bad_cfg = deepcopy(cfg)
    bad_cfg.update({{
        "instance_type": list(INSTANCE_TYPES.keys())[0],
    }})
    # We compare against a fixed baseline score of 0.40
    BASELINE_SCORE = 0.40

    return {{
        "cost":          round(cost, 2),
        "p50_ms":        perf["p50_ms"],
        "p99_ms":        perf["p99_ms"],
        "throughput_rps": perf["throughput_rps"],
        "reliability":   perf["reliability"],
        "weighted_score": ws,
        "checks": {{
            "cost_within_budget":        cost <= BUDGET_PER_MONTH,
            "p50_meets_target":          perf["p50_ms"]         <= P50_TARGET_MS,
            "p99_meets_target":          perf["p99_ms"]         <= P99_TARGET_MS,
            "throughput_meets_target":   perf["throughput_rps"] >= THROUGHPUT_TARGET_RPS,
            "reliability_above_threshold": perf["reliability"]  >= RELIABILITY_TARGET,
            "score_above_baseline":      ws                     >= BASELINE_SCORE,
            "not_over_provisioned":      cost                   <= BUDGET_PER_MONTH * 0.95,
        }},
    }}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cost/Performance simulator")
    parser.add_argument("--config", default="config.json",
                        help="Path to config JSON (default: config.json)")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 if all targets met, else 1")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    result = check_all(cfg)
    checks = result["checks"]

    print(f"=== {sys_cfg["system_type"].upper()} COST/PERFORMANCE REPORT ===")
    print()
    print(f"Monthly Cost:      ${{result['cost']:.2f}} / ${{BUDGET_PER_MONTH:.0f}} budget")
    print(f"p50 Latency:       {{result['p50_ms']:.1f}} ms  (target: <{{P50_TARGET_MS}} ms)")
    print(f"p99 Latency:       {{result['p99_ms']:.1f}} ms  (target: <{{P99_TARGET_MS}} ms)")
    print(f"Throughput:        {{result['throughput_rps']:.1f}} rps (target: >{{THROUGHPUT_TARGET_RPS}} rps)")
    print(f"Reliability:       {{result['reliability']:.4f}}  (target: >{{RELIABILITY_TARGET}})")
    print(f"Weighted Score:    {{result['weighted_score']:.4f}}")
    print()
    print("=== CHECK RESULTS ===")
    all_pass = True
    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {{status}}  {{name}}")
        if not passed:
            all_pass = False
    print()
    if all_pass:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")

    if args.check:
        sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
'''

        return files

    # ------------------------------------------------------------------
    # Spec / brief generators
    # ------------------------------------------------------------------
    def _generate_spec(self, sys_cfg: dict) -> str:
        stype = sys_cfg["system_type"]
        desc  = sys_cfg["description"]
        budget = sys_cfg["budget_per_month"]
        p50_t  = sys_cfg["p50_target_ms"]
        p99_t  = sys_cfg["p99_target_ms"]
        tput_t = sys_cfg["throughput_target_rps"]
        rel_t  = sys_cfg["reliability_target"]
        w      = sys_cfg["weights"]
        itype_lines = "\n".join(
            f"  - `{k}`: {v['vcpu']} vCPU, {v['ram_gb']} GB RAM — ${v['cost_per_month']:.0f}/mo"
            for k, v in sys_cfg["instance_types"].items()
        )
        stor_cost = sys_cfg["storage_cost_per_gb"]
        bw_cost   = sys_cfg["bandwidth_cost_per_gb"]
        base_stor = sys_cfg["base_storage_gb"]
        base_bw   = sys_cfg["base_bandwidth_gb"]

        return f"""# NEG2: Cost vs Performance Optimization

## System Under Optimization
**Type**: {stype} — {desc}

## Cost Model

### Instance Types
{itype_lines}

### Additional Costs
- Storage: ${stor_cost}/GB/month (baseline {base_stor} GB fixed)
- Bandwidth: ${bw_cost}/GB/month (baseline {base_bw} GB fixed)

### Monthly Cost Formula
```
total_cost = instance_cost_per_month * instance_count
           + {base_stor} * {stor_cost}   # storage (fixed)
           + {base_bw} * {bw_cost}  # bandwidth (fixed)
```

### Budget Constraint
**Hard cap: ${budget}/month.** Any configuration exceeding this budget receives a cost score of 0 regardless of performance.

## Performance Targets (ALL must be met)

| Metric | Target |
|--------|--------|
| p50 latency | < {p50_t} ms |
| p99 latency | < {p99_t} ms |
| Throughput | > {tput_t} rps |
| Reliability | > {rel_t} |

## Scoring Rubric

The overall score is a weighted average of three sub-scores, each in [0, 1]:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Performance | {int(w["performance"]*100)}% | How far below each latency/throughput target |
| Cost | {int(w["cost"]*100)}% | How much of the budget is used (lower spend = higher score) |
| Reliability | {int(w["reliability"]*100)}% | How far above the reliability threshold |

### Performance Sub-Score
- Each of p50, p99, throughput contributes equally (⅓ each)
- Missing any hard target multiplies the sub-score by 0.5 (penalty)

### Cost Sub-Score
- Spending 0% of budget → 1.0
- Spending 100% of budget → 0.5
- Exceeding budget → 0.0

### Reliability Sub-Score
- Below threshold: proportional credit × 0.5
- Above threshold: bonus up to 1.0

### Baseline Score
The current suboptimal `config.json` scores approximately **0.40**. Your optimized configuration must score **above 0.40** to pass the baseline check.

## Configuration Knobs

Edit `config.json` to adjust:

| Parameter | Type | Effect |
|-----------|------|--------|
| `instance_type` | enum: small/medium/large/xlarge | Determines per-instance cost, vCPU, RAM |
| `instance_count` | integer ≥ 1 | Number of instances; affects cost, throughput, latency, reliability |
| `cache_size_mb` | integer ≥ 0 | In-memory cache per node; reduces latency and backend calls |
| `thread_count` | integer ≥ 1 | Worker threads per instance; increases parallelism |
| `batch_size` | integer ≥ 1 | Requests batched together; improves throughput, slightly reduces latency |
| `connection_pool_size` | integer ≥ 1 | Concurrent connections per instance; limits queuing |
| `enable_compression` | boolean | Reduces bandwidth; slight CPU cost, net latency benefit |
| `enable_keep_alive` | boolean | Connection reuse; reduces p50 by ~15%, improves reliability |

## Deliverables
1. An updated `config.json` that satisfies **all** of the following checks:
   - `cost_within_budget`: total monthly cost ≤ ${budget}
   - `p50_meets_target`: simulated p50 ≤ {p50_t} ms
   - `p99_meets_target`: simulated p99 ≤ {p99_t} ms
   - `throughput_meets_target`: simulated throughput ≥ {tput_t} rps
   - `reliability_above_threshold`: simulated reliability ≥ {rel_t}
   - `score_above_baseline`: weighted score > 0.40
   - `not_over_provisioned`: cost ≤ ${budget * 0.95:.0f} (95% of budget — penalises waste)

2. Verify by running: `python simulator.py --check`

## Common Traps
- **Over-provisioning**: Using xlarge instances satisfies performance targets but busts the budget — cost score drops to 0.
- **Under-provisioning**: Using small instances keeps cost low but misses latency/throughput targets — performance penalty halves the sub-score.
- **Ignoring knobs**: Cache, threads, batch size, and keep-alive are free (no cost impact) but substantially improve performance — failing to tune them wastes budget on extra instances.
- **Not over-provisioned check**: Spending 95–100% of budget is flagged as wasteful even if cost is technically within budget.
"""

    def _generate_brief(self, sys_cfg: dict) -> str:
        stype  = sys_cfg["system_type"]
        budget = sys_cfg["budget_per_month"]
        p50_t  = sys_cfg["p50_target_ms"]
        p99_t  = sys_cfg["p99_target_ms"]
        tput_t = sys_cfg["throughput_target_rps"]
        rel_t  = sys_cfg["reliability_target"]
        return f"""# NEG2: Cost vs Performance Optimization (Brief)

The {stype} configuration is suboptimal. Optimize it.

Budget: ${budget}/month. Targets: p50 < {p50_t}ms, p99 < {p99_t}ms, throughput > {tput_t} rps, reliability > {rel_t}.

Edit `config.json`, then verify with `python simulator.py --check`.
"""
