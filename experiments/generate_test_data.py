#!/usr/bin/env python3
"""
Generate synthetic data for testing statistical analysis.
This creates realistic-looking experiment results to validate our analysis pipeline.
"""

import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

def generate_synthetic_results(output_dir: str = "experiments/controlled_results"):
    """Generate synthetic experiment results for testing"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Model capability scores (realistic values)
    models = {
        "gpt-4": 85,
        "claude-3-opus": 88,
        "gpt-4o": 83,
        "claude-3-sonnet": 79,
        "gpt-4o-mini": 72,
        "claude-3-haiku": 68
    }
    
    tasks = [f"TASK_{i:03d}" for i in range(1, 21)]  # 20 tasks
    conditions = ["oracle-1x", "oracle-3x", "team-standard"]
    
    print(f"Generating synthetic data for:")
    print(f"  Models: {len(models)}")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Conditions: {len(conditions)}")
    print(f"  Total: {len(models) * len(tasks) * len(conditions)} experiments")
    
    results = []
    
    for model, capability in models.items():
        for task in tasks:
            for condition in conditions:
                # Simulate scaling relationship: weaker models benefit more from teamwork
                base_performance = 0.3 + (capability - 60) * 0.01  # Base capability effect
                
                if condition == "oracle-1x":
                    # Baseline performance
                    success_prob = base_performance
                elif condition == "oracle-3x":
                    # 3x compute helps, but with diminishing returns
                    compute_boost = 0.15 * (90 - capability) / 30  # Weaker models benefit more
                    success_prob = base_performance + compute_boost
                elif condition == "team-standard":
                    # Team coordination benefit (stronger for weaker models)
                    team_boost = 0.25 * (90 - capability) / 30
                    success_prob = base_performance + team_boost
                
                # Add noise
                success_prob += random.gauss(0, 0.1)
                success_prob = max(0.05, min(0.95, success_prob))  # Clamp to reasonable range
                
                # Generate binary success
                success = random.random() < success_prob
                score = 1.0 if success else 0.0
                
                # Simulate token usage
                base_tokens = random.randint(8000, 15000)
                if condition == "oracle-3x":
                    tokens = base_tokens * 3
                elif condition == "team-standard":
                    tokens = base_tokens * 2.5  # Team uses more tokens
                else:
                    tokens = base_tokens
                
                result = {
                    "task_id": task,
                    "model": model,
                    "condition": condition,
                    "score": score,
                    "success": success,
                    "capability": capability,
                    "input_tokens": int(tokens * 0.7),
                    "output_tokens": int(tokens * 0.3),
                    "api_calls": random.randint(3, 8),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                results.append(result)
                
                # Save individual file (as expected by rigorous_statistics.py)
                filename = f"{task}_{model}_{condition}.json"
                with open(output_path / filename, 'w') as f:
                    json.dump(result, f, indent=2)
    
    print(f"Generated {len(results)} experiment results")
    
    # Also save consolidated file for analysis
    with open(output_path / "all_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Calculate some statistics for verification
    by_model = {}
    for result in results:
        model = result["model"]
        if model not in by_model:
            by_model[model] = {"oracle_score": [], "team_score": [], "capability": result["capability"]}
        
        if result["condition"] == "oracle-1x":
            by_model[model]["oracle_score"].append(result["score"])
        elif result["condition"] == "team-standard":
            by_model[model]["team_score"].append(result["score"])
    
    print("\nSynthetic scaling preview:")
    for model, data in by_model.items():
        if data["oracle_score"] and data["team_score"]:
            oracle_avg = np.mean(data["oracle_score"])
            team_avg = np.mean(data["team_score"])
            benefit = team_avg - oracle_avg
            capability = data["capability"]
            print(f"  {model} (cap={capability}): oracle={oracle_avg:.2f}, team={team_avg:.2f}, benefit={benefit:.3f}")
    
    return results

if __name__ == "__main__":
    results = generate_synthetic_results()
    print("\nSynthetic data generation complete!")
    print("Run: python analysis/rigorous_statistics.py")