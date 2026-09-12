#!/usr/bin/env python3
"""
Practical pilot experiment with affordable models.
Focus on proving the methodology with budget-friendly choices.
"""

import json
from experiments.model_configs import MODEL_CONFIGS

def design_practical_pilot():
    """Design an affordable but scientifically valid pilot"""
    
    # Select models to cover capability spectrum affordably
    pilot_models = [
        # High capability (one expensive model for reference)
        MODEL_CONFIGS[1],  # gpt-4o ($24k for full experiment)
        
        # Mid-tier affordable models
        MODEL_CONFIGS[4],  # gpt-4o-mini ($855 for full)
        MODEL_CONFIGS[6],  # gemini-1.5-flash ($1995 for full)
        
        # Budget models
        MODEL_CONFIGS[8],  # claude-3-haiku ($1650 for full)
        MODEL_CONFIGS[11], # deepseek-coder ($546 for full)
    ]
    
    # Minimal viable experiment
    n_tasks = 20  # Still enough for statistics
    n_conditions = 3  # Essential: oracle-1x, oracle-3x, team-standard
    avg_tokens_per_run = 10000  # Conservative estimate
    input_ratio = 0.7
    
    total_runs = len(pilot_models) * n_tasks * n_conditions
    
    print("=== PRACTICAL PILOT DESIGN ===")
    print(f"Models: {len(pilot_models)}")
    print(f"Tasks: {n_tasks}")  
    print(f"Conditions: {n_conditions}")
    print(f"Total runs: {total_runs}")
    print()
    
    total_cost = 0
    for model in pilot_models:
        runs = n_tasks * n_conditions
        input_tokens = avg_tokens_per_run * input_ratio
        output_tokens = avg_tokens_per_run * (1 - input_ratio)
        
        cost = runs * (
            input_tokens * model.cost_per_1k_input / 1000 +
            output_tokens * model.cost_per_1k_output / 1000
        )
        
        total_cost += cost
        print(f"{model.name:<30} ${cost:>7.2f} (cap: {model.capability_score})")
    
    print(f"{'TOTAL PILOT COST':<30} ${total_cost:>7.2f}")
    print()
    
    # Statistical power analysis
    capability_range = max(m.capability_score for m in pilot_models) - min(m.capability_score for m in pilot_models)
    print(f"Capability range: {capability_range:.1f} points")
    print(f"Experiments per model: {n_tasks * n_conditions}")
    print(f"Expected statistical power: {'Good' if capability_range > 15 and total_runs > 200 else 'Moderate'}")
    print()
    
    # Value proposition
    cost_per_model = total_cost / len(pilot_models)
    print(f"Cost per model tested: ${cost_per_model:.2f}")
    print(f"Cost per scaling point: ${total_cost / capability_range:.2f}")
    
    if total_cost < 500:
        budget_tier = "EXCELLENT"
    elif total_cost < 1500:
        budget_tier = "GOOD" 
    elif total_cost < 3000:
        budget_tier = "ACCEPTABLE"
    else:
        budget_tier = "HIGH"
    
    print(f"Budget assessment: {budget_tier}")
    
    # Recommendations
    print("\nRECOMMENDATION:")
    if total_cost < 1000:
        print("✓ Proceed with this pilot design")
        print("✓ Should provide clear evidence for scaling effects")
        print("✓ Affordable enough to run immediately")
    else:
        print("⚠ Consider further reductions:")
        print("  - Use only 4 models (remove most expensive)")
        print("  - Reduce to 15 tasks")
        print("  - Test on subset first")
    
    return {
        "models": [
            {
                "name": m.name,
                "capability": m.capability_score,
                "cost_estimate": n_tasks * n_conditions * avg_tokens_per_run * (
                    input_ratio * m.cost_per_1k_input / 1000 +
                    (1 - input_ratio) * m.cost_per_1k_output / 1000
                )
            }
            for m in pilot_models
        ],
        "experiment_design": {
            "n_tasks": n_tasks,
            "n_conditions": n_conditions, 
            "total_runs": total_runs,
            "total_cost": total_cost,
            "budget_tier": budget_tier
        }
    }

def create_execution_plan():
    """Create step-by-step execution plan for pilot"""
    
    plan = {
        "phase_1": {
            "goal": "Infrastructure validation",
            "duration": "1-2 days",
            "tasks": [
                "Test adapters with 3 models on 5 tasks",
                "Validate compute tracking",
                "Ensure statistical analysis works",
                "Estimate actual token usage"
            ]
        },
        "phase_2": {
            "goal": "Mini-pilot", 
            "duration": "1 day",
            "tasks": [
                "Run 3 models × 10 tasks × 3 conditions = 90 experiments",
                "Cost: ~$50-100 estimated",
                "Validate scaling signal detection",
                "Check variance levels"
            ]
        },
        "phase_3": {
            "goal": "Full pilot",
            "duration": "2-3 days", 
            "tasks": [
                "Run 5 models × 20 tasks × 3 conditions = 300 experiments",
                "Cost: ~$300-800 estimated",
                "Complete statistical analysis",
                "Generate scaling law coefficients"
            ]
        },
        "deliverables": [
            "Scaling law: benefit = α × capability^β",
            "Statistical significance tests",
            "Confidence intervals", 
            "Infrastructure validation report",
            "Cost projections for larger studies"
        ]
    }
    
    return plan

if __name__ == "__main__":
    design = design_practical_pilot()
    
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    
    execution_plan = create_execution_plan()
    
    for phase, details in execution_plan.items():
        if phase.startswith("phase"):
            print(f"\n{phase.upper()}: {details['goal']}")
            print(f"Duration: {details['duration']}")
            for task in details['tasks']:
                print(f"  • {task}")
    
    print(f"\nFinal deliverables:")
    for deliverable in execution_plan['deliverables']:
        print(f"  ✓ {deliverable}")
    
    # Save design
    with open("experiments/practical_pilot_design.json", "w") as f:
        json.dump({
            "design": design,
            "execution_plan": execution_plan
        }, f, indent=2)
    
    print(f"\nPilot design saved to experiments/practical_pilot_design.json")