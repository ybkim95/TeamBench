#!/usr/bin/env python3
"""
Realistic budget analysis for TeamBench scaling experiments.
"""

import json
from experiments.model_configs import MODEL_CONFIGS

def calculate_realistic_budget():
    """Calculate realistic experiment costs"""
    
    # Select cost-effective models that still cover the capability spectrum
    selected_models = [
        # Frontier (pick 2 most important)
        MODEL_CONFIGS[2],  # claude-3-opus (highest capability)
        MODEL_CONFIGS[1],  # gpt-4o (good balance)
        
        # Mid-tier (pick 3 for scaling curve) 
        MODEL_CONFIGS[4],  # gpt-4o-mini
        MODEL_CONFIGS[5],  # claude-3-sonnet
        MODEL_CONFIGS[6],  # gemini-1.5-flash
        
        # Accessible (pick 2 weakest for contrast)
        MODEL_CONFIGS[8],  # claude-3-haiku  
        MODEL_CONFIGS[11], # deepseek-coder-v2-lite
    ]
    
    # Experimental design
    n_tasks = 50  # Reduced from 70 
    n_conditions = 5  # oracle-1x, oracle-3x, team-standard, team-budget-matched, oracle-retry-3
    avg_tokens_per_run = 12000  # Conservative estimate
    input_ratio = 0.7
    
    total_runs = len(selected_models) * n_tasks * n_conditions
    
    print("=== REALISTIC BUDGET ANALYSIS ===")
    print(f"Selected models: {len(selected_models)}")
    print(f"Tasks: {n_tasks}")
    print(f"Conditions: {n_conditions}")
    print(f"Total runs: {total_runs}")
    print(f"Avg tokens per run: {avg_tokens_per_run}")
    print()
    
    # Calculate costs per model
    total_cost = 0
    breakdown = {}
    
    for model in selected_models:
        runs_per_model = n_tasks * n_conditions
        input_tokens = avg_tokens_per_run * input_ratio
        output_tokens = avg_tokens_per_run * (1 - input_ratio)
        
        input_cost = (input_tokens * runs_per_model) * (model.cost_per_1k_input / 1000)
        output_cost = (output_tokens * runs_per_model) * (model.cost_per_1k_output / 1000)
        model_total = input_cost + output_cost
        
        breakdown[model.name] = {
            "runs": runs_per_model,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total": model_total,
            "capability": model.capability_score
        }
        
        total_cost += model_total
        
        print(f"{model.name:<30} ${model_total:>8.2f} (cap: {model.capability_score})")
    
    print(f"{'TOTAL':<30} ${total_cost:>8.2f}")
    print()
    
    # Analysis
    print("BUDGET TIERS:")
    
    if total_cost < 1000:
        tier = "FEASIBLE"
        recommendation = "Proceed with full experiment"
    elif total_cost < 3000:
        tier = "ACCEPTABLE" 
        recommendation = "Proceed with careful monitoring"
    elif total_cost < 10000:
        tier = "HIGH"
        recommendation = "Consider reducing scope or using cheaper models"
    else:
        tier = "PROHIBITIVE"
        recommendation = "Must reduce scope significantly"
    
    print(f"Budget tier: {tier}")
    print(f"Recommendation: {recommendation}")
    print(f"Cost per insight: ${total_cost / (len(selected_models) - 1):.2f}")  # Cost per capability point measured
    
    # Alternative scenarios
    print("\nALTERNATIVE SCENARIOS:")
    
    # Scenario 1: Cheaper models only
    cheap_models = [m for m in selected_models if m.cost_per_1k_input < 1.0]
    if cheap_models:
        cheap_cost = sum(
            n_tasks * n_conditions * avg_tokens_per_run * (
                input_ratio * m.cost_per_1k_input / 1000 +
                (1 - input_ratio) * m.cost_per_1k_output / 1000
            )
            for m in cheap_models
        )
        print(f"Cheap models only ({len(cheap_models)} models): ${cheap_cost:.2f}")
    
    # Scenario 2: Fewer tasks
    reduced_cost = total_cost * (30 / n_tasks)
    print(f"Reduced to 30 tasks: ${reduced_cost:.2f}")
    
    # Scenario 3: Fewer conditions
    essential_cost = total_cost * (3 / n_conditions)  # oracle-1x, oracle-3x, team-standard only
    print(f"Essential conditions only: ${essential_cost:.2f}")
    
    return {
        "total_cost": total_cost,
        "tier": tier,
        "recommendation": recommendation,
        "breakdown": breakdown,
        "experiment_params": {
            "models": len(selected_models),
            "tasks": n_tasks,
            "conditions": n_conditions,
            "total_runs": total_runs
        }
    }

def save_budget_report(analysis):
    """Save budget analysis to file"""
    
    with open("experiments/budget_report.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    # Create human-readable report
    report = []
    report.append("# TeamBench Budget Analysis")
    report.append("")
    report.append(f"**Total Cost**: ${analysis['total_cost']:.2f}")
    report.append(f"**Budget Tier**: {analysis['tier']}")
    report.append(f"**Recommendation**: {analysis['recommendation']}")
    report.append("")
    report.append("## Experiment Parameters")
    params = analysis['experiment_params']
    report.append(f"- Models: {params['models']}")
    report.append(f"- Tasks: {params['tasks']}")
    report.append(f"- Conditions: {params['conditions']}")
    report.append(f"- Total runs: {params['total_runs']}")
    report.append("")
    report.append("## Cost Breakdown by Model")
    for model, data in analysis['breakdown'].items():
        report.append(f"- {model}: ${data['total']:.2f} ({data['runs']} runs)")
    
    with open("experiments/budget_report.md", "w") as f:
        f.write("\n".join(report))
    
    print("Budget report saved to experiments/budget_report.md")

if __name__ == "__main__":
    analysis = calculate_realistic_budget()
    save_budget_report(analysis)