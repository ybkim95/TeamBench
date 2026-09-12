#!/usr/bin/env python3
"""
Model configurations for rigorous scaling experiments.
Based on actual API pricing and capability benchmarks.
"""

from typing import List, Dict, Optional
from pathlib import Path
import os
import json
from harness.schemas import ModelConfig

# Latest pricing as of March 2025 (USD per 1M tokens)
MODEL_CONFIGS = [
    # Tier 1: Frontier Models
    ModelConfig(
        name="gpt-4-turbo-2024-04-09",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        params_estimate="~1.7T",
        cost_per_1k_input=10.0,  # $10/1M = $0.01/1K
        cost_per_1k_output=30.0,  # $30/1M = $0.03/1K
        capability_score=87.5,
        max_context=128000,
        supports_tools=True
    ),
    ModelConfig(
        name="gpt-4o",
        provider="openai", 
        api_key_env="OPENAI_API_KEY",
        params_estimate="~500B",
        cost_per_1k_input=5.0,
        cost_per_1k_output=15.0,
        capability_score=85.2,
        max_context=128000,
        supports_tools=True
    ),
    ModelConfig(
        name="claude-3-opus-20240229",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        params_estimate="~1T",
        cost_per_1k_input=15.0,
        cost_per_1k_output=75.0,
        capability_score=88.9,  # Highest on many coding benchmarks
        max_context=200000,
        supports_tools=True
    ),
    ModelConfig(
        name="gemini-1.5-pro-preview-0514",
        provider="google",
        api_key_env="GOOGLE_AI_API_KEY",
        params_estimate="~1T",
        cost_per_1k_input=7.0,
        cost_per_1k_output=21.0,
        capability_score=84.1,
        max_context=1000000,  # 1M context
        supports_tools=True
    ),
    
    # Tier 2: Mid-Tier Models
    ModelConfig(
        name="gpt-4o-mini",
        provider="openai",
        api_key_env="OPENAI_API_KEY", 
        params_estimate="~100B",
        cost_per_1k_input=0.15,
        cost_per_1k_output=0.60,
        capability_score=75.8,
        max_context=128000,
        supports_tools=True
    ),
    ModelConfig(
        name="claude-3-sonnet-20240229",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        params_estimate="~200B",
        cost_per_1k_input=3.0,
        cost_per_1k_output=15.0,
        capability_score=79.3,
        max_context=200000,
        supports_tools=True
    ),
    ModelConfig(
        name="gemini-1.5-flash",
        provider="google",
        api_key_env="GOOGLE_AI_API_KEY",
        params_estimate="~100B",
        cost_per_1k_input=0.35,
        cost_per_1k_output=1.40,
        capability_score=73.1,
        max_context=1000000,
        supports_tools=True
    ),
    ModelConfig(
        name="mixtral-8x7b-32768",
        provider="mistral",
        api_key_env="MISTRAL_API_KEY",
        params_estimate="47B",
        cost_per_1k_input=0.70,
        cost_per_1k_output=0.70,
        capability_score=71.4,
        max_context=32768,
        supports_tools=True
    ),
    
    # Tier 3: Accessible Models
    ModelConfig(
        name="claude-3-haiku-20240307",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        params_estimate="~50B",
        cost_per_1k_input=0.25,
        cost_per_1k_output=1.25,
        capability_score=68.2,
        max_context=200000,
        supports_tools=True
    ),
    ModelConfig(
        name="llama-3.1-70b-versatile",
        provider="groq",  # Using Groq for fast inference
        api_key_env="GROQ_API_KEY",
        params_estimate="70B",
        cost_per_1k_input=0.59,
        cost_per_1k_output=0.79,
        capability_score=69.8,
        max_context=128000,
        supports_tools=False  # Limited tool support
    ),
    ModelConfig(
        name="qwen2.5-72b-instruct",
        provider="together", 
        api_key_env="TOGETHER_API_KEY",
        params_estimate="72B",
        cost_per_1k_input=0.40,
        cost_per_1k_output=0.40,
        capability_score=67.5,
        max_context=32768,
        supports_tools=True
    ),
    ModelConfig(
        name="deepseek-coder-v2-lite-instruct",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        params_estimate="16B",
        cost_per_1k_input=0.14,
        cost_per_1k_output=0.28,
        capability_score=65.9,
        max_context=128000,
        supports_tools=True
    )
]

def get_available_models() -> List[ModelConfig]:
    """Return models with available API keys"""
    available = []
    
    for model in MODEL_CONFIGS:
        if model.api_key_env and os.environ.get(model.api_key_env):
            available.append(model)
        elif not model.api_key_env:
            # For testing/simulation
            available.append(model)
    
    return available

def get_models_by_tier() -> Dict[str, List[ModelConfig]]:
    """Group models by capability tier for analysis"""
    
    tiers = {
        "frontier": [],  # 80+
        "mid_tier": [],  # 70-80
        "accessible": []  # <70
    }
    
    for model in MODEL_CONFIGS:
        if model.capability_score >= 80:
            tiers["frontier"].append(model)
        elif model.capability_score >= 70:
            tiers["mid_tier"].append(model)
        else:
            tiers["accessible"].append(model)
    
    return tiers

def estimate_cost(models: List[ModelConfig], 
                  tasks: int, 
                  conditions: int,
                  avg_tokens_per_run: int = 15000,
                  input_ratio: float = 0.7) -> Dict:
    """Estimate total experimental cost"""
    
    total_runs = len(models) * tasks * conditions
    input_tokens = avg_tokens_per_run * input_ratio
    output_tokens = avg_tokens_per_run * (1 - input_ratio)
    
    cost_breakdown = {}
    total_cost = 0
    
    for model in models:
        runs_per_model = tasks * conditions
        model_input_cost = (input_tokens * runs_per_model) * (model.cost_per_1k_input / 1000)
        model_output_cost = (output_tokens * runs_per_model) * (model.cost_per_1k_output / 1000)
        model_total = model_input_cost + model_output_cost
        
        cost_breakdown[model.name] = {
            "runs": runs_per_model,
            "input_cost": model_input_cost,
            "output_cost": model_output_cost,
            "total": model_total
        }
        
        total_cost += model_total
    
    return {
        "total_cost_usd": total_cost,
        "total_runs": total_runs,
        "avg_cost_per_run": total_cost / total_runs,
        "breakdown": cost_breakdown,
        "assumptions": {
            "avg_tokens_per_run": avg_tokens_per_run,
            "input_ratio": input_ratio
        }
    }

def check_api_access() -> Dict[str, bool]:
    """Check which model APIs are accessible"""
    
    access_status = {}
    
    for model in MODEL_CONFIGS:
        if model.api_key_env:
            has_key = bool(os.environ.get(model.api_key_env))
            access_status[model.name] = has_key
            
            if has_key:
                print(f"✓ {model.name}: API key found")
            else:
                print(f"✗ {model.name}: Missing {model.api_key_env}")
        else:
            access_status[model.name] = False
            print(f"⚠ {model.name}: No API key configured")
    
    available_count = sum(access_status.values())
    print(f"\nTotal available models: {available_count}/{len(MODEL_CONFIGS)}")
    
    return access_status

def save_model_manifest(output_path: str = "experiments/model_manifest.json"):
    """Save model configurations to JSON for reference"""
    
    manifest = {
        "generated": "2025-03-30",
        "models": [model.to_dict() for model in MODEL_CONFIGS],
        "tiers": {tier: [m.name for m in models] 
                 for tier, models in get_models_by_tier().items()},
        "cost_estimate": estimate_cost(MODEL_CONFIGS[:8], 70, 5)  # Conservative estimate
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Model manifest saved to {output_path}")

if __name__ == "__main__":
    print("=== TeamBench Model Configuration ===\n")
    
    print("Checking API access...")
    access = check_api_access()
    
    print("\nModel tiers:")
    for tier, models in get_models_by_tier().items():
        print(f"  {tier}: {[m.name for m in models]}")
    
    print("\nCost estimate (8 models, 70 tasks, 5 conditions):")
    cost = estimate_cost(MODEL_CONFIGS[:8], 70, 5)
    print(f"  Total cost: ${cost['total_cost_usd']:.2f}")
    print(f"  Cost per run: ${cost['avg_cost_per_run']:.4f}")
    print(f"  Total runs: {cost['total_runs']}")
    
    save_model_manifest()