#!/usr/bin/env python3
"""Open-source model evaluation v2 — with correct vLLM tool-call parsers.

Previous open-source experiments failed due to:
1. Wrong tool-call parser (generic instead of model-specific)
2. max_model_len=8192 too short (context overflow)

This script uses the correct vLLM serve flags for each model.

Models (ranked by expected reliability):
1. Qwen2.5-Coder-32B-Instruct  (hermes parser, dense, most reliable)
2. GLM-4.5-Air-FP8              (glm45 parser, MoE 106B/12B active)
3. Qwen3-Coder-30B-A3B-FP8     (qwen3_coder parser, MoE 30B/3B active)

Usage:
    # Step 1: Start the vLLM server for a model
    bash scripts/serve_opensource_v2.sh qwen25-coder

    # Step 2: Run evaluation
    python scripts/run_opensource_v2.py --model qwen25-coder-32b
    python scripts/run_opensource_v2.py --model glm45-air
    python scripts/run_opensource_v2.py --model qwen3-coder-30b
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

# 28-task Mini subset
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

CONDITIONS = [
    AblationCondition.ORACLE,
    AblationCondition.RESTRICTED,
    AblationCondition.TEAM_NO_VERIFY,
    AblationCondition.TEAM_NO_PLAN,
    AblationCondition.FULL,
]

# Model configs — the adapter uses OpenAI-compatible API pointed at local vLLM
MODEL_CONFIGS = {
    "qwen25-coder-32b": {
        "model_name": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "output": "crossmodel_qwen25_coder_32b_seed0.json",
        "description": "Qwen2.5-Coder-32B (hermes parser, dense)",
    },
    "glm45-air": {
        "model_name": "zai-org/GLM-4.5-Air-FP8",
        "output": "crossmodel_glm45_air_seed0.json",
        "description": "GLM-4.5-Air (glm45 parser, MoE 106B/12B)",
    },
    "qwen3-coder-30b": {
        "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8",
        "output": "crossmodel_qwen3_coder_30b_v2_seed0.json",
        "description": "Qwen3-Coder-30B FP8 (qwen3_coder parser, MoE 30B/3B)",
    },
    "llama4-scout": {
        "model_name": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "output": "crossmodel_llama4_scout_seed0.json",
        "description": "Llama-4-Scout (llama3_json parser, MoE 109B/17B)",
    },
    "devstral-24b": {
        "model_name": "mistralai/Devstral-Small-2-24B-Instruct-2512",
        "output": "crossmodel_devstral_24b_seed0.json",
        "description": "Devstral-Small-2-24B (mistral parser, Mistral agentic coder)",
    },
    "glm45-air": {
        "model_name": "zai-org/GLM-4.5-Air-FP8",
        "output": "crossmodel_glm45_air_seed0.json",
        "description": "GLM-4.5-Air (glm45 parser, MoE 106B/12B active)",
    },
    "llama4-scout-fp8": {
        "model_name": "RedHatAI/Llama-4-Scout-17B-16E-Instruct-FP8-dynamic",
        "output": "crossmodel_llama4_scout_seed0.json",
        "description": "Llama-4-Scout FP8 (llama3_json parser, Meta MoE 109B/17B)",
    },
    "deepseek-r1-llama-70b": {
        "model_name": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "output": "crossmodel_deepseek_r1_llama70b_seed0.json",
        "description": "DeepSeek-R1-Distill-Llama-70B (hermes parser, 70B dense)",
    },
    "gemma3-27b": {
        "model_name": "google/gemma-3-27b-it",
        "output": "crossmodel_gemma3_27b_seed0.json",
        "description": "Gemma-3-27B-IT (hermes parser, Google 27B dense)",
    },
    "devstral2-123b": {
        "model_name": "cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit",
        "output": "crossmodel_devstral2_123b_seed0.json",
        "description": "Devstral-2-123B AWQ-4bit (mistral parser, Mistral 123B)",
    },
    "gpt-oss-20b": {
        "model_name": "openai/gpt-oss-20b",
        "output": "crossmodel_gpt_oss_20b_seed0.json",
        "description": "GPT-OSS-20B (OpenAI open-weight, MoE 21B/3.6B active)",
    },
    "gpt-oss-120b": {
        "model_name": "openai/gpt-oss-120b",
        "output": "crossmodel_gpt_oss_120b_seed0.json",
        "description": "GPT-OSS-120B (OpenAI open-weight, MoE 117B/5.1B active)",
    },
    "codegemma-7b-it": {
        "model_name": "google/codegemma-7b-it",
        "output": "crossmodel_codegemma_7b_it_seed0.json",
        "description": "CodeGemma-7B-IT (Google, code-specialized 7B)",
    },
    "codegemma-7b": {
        "model_name": "google/codegemma-7b",
        "output": "crossmodel_codegemma_7b_seed0.json",
        "description": "CodeGemma-7B (Google, code-specialized 7B base)",
    },
    "codegemma-2b": {
        "model_name": "google/codegemma-2b",
        "output": "crossmodel_codegemma_2b_seed0.json",
        "description": "CodeGemma-2B (Google, code-specialized 2B)",
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODEL_CONFIGS.keys()))
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--api-base", default="http://localhost:8000/v1",
                    help="vLLM server endpoint")
    args = ap.parse_args()

    cfg = MODEL_CONFIGS[args.model]
    outpath = os.path.join("shared", "ablation_results", cfg["output"])

    print(f"Open-Source Evaluation v2")
    print(f"Model: {cfg['description']}")
    print(f"API Base: {args.api_base}")
    print(f"Tasks: {len(TASKS)}")
    print(f"Conditions: {len(CONDITIONS)}")
    print("=" * 60)

    # Use vllm: prefix so the adapter routes to OpenAIAdapter with local base_url
    model_str = f"vllm:{cfg['model_name']}@{args.api_base}"
    print(f"Adapter model string: {model_str}")

    run_full_ablation(
        model=model_str,
        tasks=TASKS,
        seeds=args.seeds,
        tasks_dir="tasks",
        output=outpath,
        conditions=CONDITIONS,
    )

    print(f"\nResults saved to {outpath}")


if __name__ == "__main__":
    main()
