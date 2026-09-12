#!/usr/bin/env python3
"""Run cross-model ablation experiments with Qwen3 models served via vLLM.

Prerequisites:
  1. Start vLLM servers (one per model):
       bash scripts/serve_vllm.sh Qwen/Qwen3-4B  1 8001
       bash scripts/serve_vllm.sh Qwen/Qwen3-8B  2 8002
       bash scripts/serve_vllm.sh Qwen/Qwen3-14B 3 8003

  2. Run experiments (sequentially or pick one model):
       python scripts/run_qwen_experiments.py --model qwen3-4b
       python scripts/run_qwen_experiments.py --model qwen3-8b
       python scripts/run_qwen_experiments.py --model qwen3-14b
       python scripts/run_qwen_experiments.py --model all

Each model runs 28 tasks x 5 conditions = 140 runs.
"""
import argparse
import os
import sys
import subprocess
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Same 28-task cross-model subset used for other models
TASKS = [
    "MULTI1_fullstack_fix", "TEST1_spec_to_tests", "O2_incident_rootcause",
    "PIPE1_etl_fix", "TRAP1_spec_conflict", "TRAP3_metric_mirage",
    "TRAP5_security_theater", "CROSS1_api_contract", "CROSS3_protocol_bridge",
    "CRYPTO1_nonce_reuse", "DIST1_queue_race", "SEC1_vuln_patch",
    "SEC3_crypto_upgrade", "D1_schema_drift", "D8_csv_cleanup",
    "TEST2_regression", "TEST5_mutation_resistant", "O1_service_health",
    "O3_log_analysis", "P1_policy_config", "P3_access_control",
    "SPEC1_feature_impl", "SPEC3_data_model", "INC1_cascade_failure",
    "INC4_dns_miscfg", "IR1_evidence_qa", "NEG1_tradeoff_config",
    "CR5_test_coverage",
]

CONDITIONS = ["oracle", "restricted", "team_no_verify", "team_no_plan", "full"]

# Model configs: (adapter_model_string, vllm_base_url, output_filename)
MODELS = {
    "qwen3-4b": {
        "adapter": "vllm:Qwen/Qwen3-4B@http://localhost:8001/v1",
        "port": 8001,
        "output": "crossmodel_qwen3_4b_seed0.json",
    },
    "qwen3-8b": {
        "adapter": "vllm:Qwen/Qwen3-8B@http://localhost:8002/v1",
        "port": 8002,
        "output": "crossmodel_qwen3_8b_seed0.json",
    },
    "qwen3-14b": {
        "adapter": "vllm:Qwen/Qwen3-14B@http://localhost:8003/v1",
        "port": 8003,
        "output": "crossmodel_qwen3_14b_seed0.json",
    },
    "qwen3.5-27b": {
        "adapter": "vllm:Qwen/Qwen3.5-27B@http://localhost:8004/v1",
        "port": 8004,
        "output": "crossmodel_qwen3.5_27b_seed0.json",
    },
    "qwen3-coder-30b": {
        "adapter": "vllm:Qwen/Qwen3-Coder-30B-A3B-Instruct@http://localhost:8005/v1",
        "port": 8005,
        "output": "crossmodel_qwen3_coder_30b_seed0.json",
    },
    "qwen3-32b": {
        "adapter": "vllm:Qwen/Qwen3-32B@http://localhost:8006/v1",
        "port": 8006,
        "output": "crossmodel_qwen3_32b_seed0.json",
    },
    "deepseek-r1-distill-32b": {
        "adapter": "vllm:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B@http://localhost:8007/v1",
        "port": 8007,
        "output": "crossmodel_deepseek_r1_distill_32b_seed0.json",
    },
}


def check_server(port: int, timeout: int = 5) -> bool:
    """Check if a vLLM server is responding on the given port."""
    try:
        r = requests.get(f"http://localhost:{port}/v1/models", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def wait_for_server(port: int, max_wait: int = 300):
    """Wait up to max_wait seconds for a vLLM server to become ready."""
    print(f"  Waiting for vLLM server on port {port}...")
    start = time.time()
    while time.time() - start < max_wait:
        if check_server(port):
            print(f"  Server on port {port} is ready!")
            return True
        time.sleep(5)
    print(f"  ERROR: Server on port {port} not ready after {max_wait}s")
    return False


def run_model(name: str, config: dict, seeds: list[int]):
    """Run ablation for a single Qwen model."""
    port = config["port"]
    if not check_server(port):
        print(f"\n[{name}] vLLM server not running on port {port}.")
        print(f"  Start it with: bash scripts/serve_vllm.sh Qwen/Qwen3-{name.split('-')[1].upper()} <gpu_id> {port}")
        return False

    outpath = os.path.join("shared", "ablation_results", config["output"])
    print(f"\n{'='*60}")
    print(f"Running {name}: {len(TASKS)} tasks x {len(CONDITIONS)} conditions x {len(seeds)} seeds")
    print(f"  Adapter: {config['adapter']}")
    print(f"  Output:  {outpath}")
    print(f"{'='*60}\n")

    from harness.ablation import run_full_ablation, AblationCondition
    conds = [AblationCondition(c) for c in CONDITIONS]
    run_full_ablation(
        model=config["adapter"],
        tasks=TASKS,
        seeds=seeds,
        tasks_dir="tasks",
        output=outpath,
        conditions=conds,
    )
    print(f"\n[{name}] Done! Results saved to {outpath}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Run Qwen3 cross-model experiments")
    ap.add_argument("--model", required=True, choices=list(MODELS.keys()) + ["all"],
                     help="Which Qwen3 model to evaluate (or 'all')")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0],
                     help="Seeds to evaluate (default: [0])")
    ap.add_argument("--check-only", action="store_true",
                     help="Only check if servers are running, don't run experiments")
    args = ap.parse_args()

    if args.model == "all":
        models_to_run = list(MODELS.items())
    else:
        models_to_run = [(args.model, MODELS[args.model])]

    if args.check_only:
        for name, config in models_to_run:
            status = "READY" if check_server(config["port"]) else "NOT RUNNING"
            print(f"  {name}: port {config['port']} -> {status}")
        return

    for name, config in models_to_run:
        run_model(name, config, args.seeds)


if __name__ == "__main__":
    main()
