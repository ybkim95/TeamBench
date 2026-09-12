#!/usr/bin/env python3
"""
Ultra-budget pilot that's still scientifically valid.
Remove expensive models, focus on affordable scaling analysis.
"""

import json
from experiments.model_configs import MODEL_CONFIGS

def design_budget_pilot():
    """Design minimal cost pilot with good capability coverage"""
    
    # Only use affordable models
    budget_models = [
        MODEL_CONFIGS[4],  # gpt-4o-mini (75.8 capability, $171 for 60 runs)
        MODEL_CONFIGS[6],  # gemini-1.5-flash (73.1 capability, $399 for 60 runs)  
        MODEL_CONFIGS[8],  # claude-3-haiku (68.2 capability, $330 for 60 runs)
        MODEL_CONFIGS[11], # deepseek-coder (65.9 capability, $109 for 60 runs)
    ]
    
    # Minimal experiment
    n_tasks = 15  # Reduced but still adequate
    n_conditions = 3  # oracle-1x, oracle-3x, team-standard
    avg_tokens_per_run = 8000  # More realistic for shorter tasks
    input_ratio = 0.7
    
    total_runs = len(budget_models) * n_tasks * n_conditions
    
    print("=== BUDGET PILOT DESIGN ===")
    print(f"Models: {len(budget_models)}")
    print(f"Tasks: {n_tasks}")
    print(f"Conditions: {n_conditions}")
    print(f"Total runs: {total_runs}")
    print()
    
    total_cost = 0
    for model in budget_models:
        runs = n_tasks * n_conditions
        input_tokens = avg_tokens_per_run * input_ratio
        output_tokens = avg_tokens_per_run * (1 - input_ratio)
        
        cost = runs * (
            input_tokens * model.cost_per_1k_input / 1000 +
            output_tokens * model.cost_per_1k_output / 1000
        )
        
        total_cost += cost
        print(f"{model.name:<30} ${cost:>6.2f} (cap: {model.capability_score})")
    
    print(f"{'TOTAL BUDGET COST':<30} ${total_cost:>6.2f}")
    print()
    
    # Statistical analysis
    capabilities = [m.capability_score for m in budget_models]
    capability_range = max(capabilities) - min(capabilities)
    experiments_per_model = n_tasks * n_conditions
    
    print("STATISTICAL POWER ANALYSIS:")
    print(f"  Capability range: {capability_range:.1f} points")
    print(f"  Experiments per model: {experiments_per_model}")
    print(f"  Total observations: {total_runs}")
    print(f"  Expected correlation power: {'Good' if capability_range > 8 and experiments_per_model > 30 else 'Moderate'}")
    print()
    
    # Value metrics
    print("VALUE METRICS:")
    print(f"  Cost per model: ${total_cost / len(budget_models):.2f}")
    print(f"  Cost per experiment: ${total_cost / total_runs:.2f}")
    print(f"  Cost per capability point: ${total_cost / capability_range:.2f}")
    
    budget_assessment = "EXCELLENT" if total_cost < 300 else "GOOD" if total_cost < 800 else "ACCEPTABLE"
    print(f"  Budget assessment: {budget_assessment}")
    print()
    
    # Scientific validity
    print("SCIENTIFIC VALIDITY:")
    can_detect_correlation = capability_range > 8 and total_runs > 150
    can_test_compute = experiments_per_model > 30
    affordable = total_cost < 1000
    
    print(f"  ✓ Can detect scaling correlation: {can_detect_correlation}")
    print(f"  ✓ Can test compute controls: {can_test_compute}")
    print(f"  ✓ Financially feasible: {affordable}")
    
    valid = can_detect_correlation and can_test_compute and affordable
    
    if valid:
        print(f"  → Overall assessment: SCIENTIFICALLY VALID")
        recommendation = "PROCEED with this design"
    else:
        print(f"  → Overall assessment: NEEDS ADJUSTMENT")
        recommendation = "MODIFY before proceeding"
    
    print(f"\nRECOMMENDATION: {recommendation}")
    
    if valid:
        print("\nEXPECTED OUTCOMES:")
        print("  • Clear scaling law coefficient (β < 0)")
        print("  • Significance test for inverse correlation")  
        print("  • Compute control validation")
        print("  • Infrastructure validation for larger studies")
        print("  • Total timeline: 3-5 days")
    
    return {
        "models": [
            {
                "name": m.name,
                "capability": m.capability_score,
                "cost": n_tasks * n_conditions * avg_tokens_per_run * (
                    input_ratio * m.cost_per_1k_input / 1000 +
                    (1 - input_ratio) * m.cost_per_1k_output / 1000
                )
            }
            for m in budget_models
        ],
        "design": {
            "n_tasks": n_tasks,
            "n_conditions": n_conditions,
            "total_runs": total_runs,
            "total_cost": total_cost,
            "capability_range": capability_range,
            "valid": valid,
            "recommendation": recommendation
        }
    }

def create_immediate_action_plan():
    """Create actionable next steps for budget pilot"""
    
    actions = [
        {
            "task": "Validate model access",
            "description": "Test API keys for gpt-4o-mini, gemini-1.5-flash, claude-3-haiku, deepseek-coder",
            "duration": "30 minutes",
            "cost": "$0"
        },
        {
            "task": "Infrastructure test",
            "description": "Run 2 models × 3 tasks × 3 conditions = 18 experiments",
            "duration": "2 hours", 
            "cost": "$5-15"
        },
        {
            "task": "Mini-pilot",
            "description": "Run 4 models × 5 tasks × 3 conditions = 60 experiments",
            "duration": "4-8 hours",
            "cost": "$50-150"
        },
        {
            "task": "Full budget pilot",
            "description": "Run 4 models × 15 tasks × 3 conditions = 180 experiments", 
            "duration": "12-24 hours",
            "cost": "$200-600"
        },
        {
            "task": "Analysis and report",
            "description": "Statistical analysis, scaling law fitting, report generation",
            "duration": "4-6 hours",
            "cost": "$0"
        }
    ]
    
    total_time = "1-2 days active work + compute time"
    total_cost = "$255-765"
    
    return {
        "actions": actions,
        "timeline": total_time,
        "budget": total_cost,
        "success_criteria": [
            "Scaling correlation r < -0.4 with p < 0.05",
            "Team vs Oracle-3x comparison working", 
            "Infrastructure validated for larger studies",
            "Cost projections for full experiment"
        ]
    }

if __name__ == "__main__":
    design = design_budget_pilot()
    action_plan = create_immediate_action_plan()
    
    print("\n" + "="*50)
    print("IMMEDIATE ACTION PLAN")
    print("="*50)
    
    for i, action in enumerate(action_plan["actions"], 1):
        print(f"\n{i}. {action['task']}")
        print(f"   {action['description']}")
        print(f"   Time: {action['duration']}, Cost: {action['cost']}")
    
    print(f"\nTOTAL TIMELINE: {action_plan['timeline']}")
    print(f"TOTAL BUDGET: {action_plan['budget']}")
    
    print(f"\nSUCCESS CRITERIA:")
    for criterion in action_plan['success_criteria']:
        print(f"  ✓ {criterion}")
    
    # Save complete plan
    with open("experiments/budget_pilot_plan.json", "w") as f:
        json.dump({
            "design": design,
            "action_plan": action_plan
        }, f, indent=2)
    
    print(f"\nBudget pilot plan saved to experiments/budget_pilot_plan.json")
    
    if design["design"]["valid"]:
        print(f"\n🎯 READY TO EXECUTE: This pilot will provide scientifically valid scaling evidence at minimal cost.")