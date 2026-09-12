#!/usr/bin/env python3
"""
Debug infrastructure issues found in validation.
"""

import json
from dataclasses import asdict
from experiments.simple_runner import SimpleExperiment

def debug_data_consistency():
    """Debug why data loading/saving is inconsistent"""
    
    print("=== DEBUGGING DATA CONSISTENCY ===")
    
    # Create test experiment
    experiment = SimpleExperiment(
        task_id="test_task",
        model="test_model", 
        condition="test_condition",
        timestamp="2024-01-01T00:00:00Z",
        success=True,
        score=1.0,
        tokens_used=1000,
        api_calls=1,
        duration_seconds=30.0
    )
    
    print("Original experiment:")
    print(f"  task_id: {experiment.task_id}")
    print(f"  model: {experiment.model}")
    print(f"  condition: {experiment.condition}")
    
    # Test different serialization approaches
    
    # Method 1: Using __dict__
    dict_data = experiment.__dict__
    print(f"\nMethod 1 (__dict__): {list(dict_data.keys())}")
    
    # Method 2: Using asdict
    try:
        asdict_data = asdict(experiment)
        print(f"Method 2 (asdict): {list(asdict_data.keys())}")
    except Exception as e:
        print(f"Method 2 failed: {e}")
        asdict_data = None
    
    # Method 3: Manual serialization
    manual_data = {
        "task_id": experiment.task_id,
        "model": experiment.model,
        "condition": experiment.condition,
        "timestamp": experiment.timestamp,
        "success": experiment.success,
        "score": experiment.score,
        "tokens_used": experiment.tokens_used,
        "api_calls": experiment.api_calls,
        "duration_seconds": experiment.duration_seconds,
        "error": experiment.error
    }
    print(f"Method 3 (manual): {list(manual_data.keys())}")
    
    # Test save/load cycle
    test_file = "experiments/test_experiment.json"
    
    for method_name, data in [("dict", dict_data), ("asdict", asdict_data), ("manual", manual_data)]:
        if data is None:
            continue
            
        try:
            # Save
            with open(test_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Load
            with open(test_file) as f:
                loaded_data = json.load(f)
            
            # Compare
            print(f"\n{method_name.upper()} method:")
            print(f"  Original keys: {sorted(data.keys())}")
            print(f"  Loaded keys: {sorted(loaded_data.keys())}")
            print(f"  task_id match: {data['task_id'] == loaded_data['task_id']}")
            print(f"  All values match: {data == loaded_data}")
            
        except Exception as e:
            print(f"{method_name.upper()} method failed: {e}")

def debug_scaling_calculation():
    """Debug why scaling correlation has wrong sign"""
    
    print("\n=== DEBUGGING SCALING CALCULATION ===")
    
    # Test with known data that SHOULD show inverse scaling
    test_data = [
        # Strong model (cap=80): low team benefit
        {"model": "strong", "capability": 80, "condition": "oracle-1x", "score": 0.8},
        {"model": "strong", "capability": 80, "condition": "team-standard", "score": 0.85},  # Small benefit
        
        # Medium model (cap=70): medium team benefit  
        {"model": "medium", "capability": 70, "condition": "oracle-1x", "score": 0.6},
        {"model": "medium", "capability": 70, "condition": "team-standard", "score": 0.75},  # Medium benefit
        
        # Weak model (cap=60): high team benefit
        {"model": "weak", "capability": 60, "condition": "oracle-1x", "score": 0.4},
        {"model": "weak", "capability": 60, "condition": "team-standard", "score": 0.7},   # Large benefit
    ]
    
    print("Test data design:")
    print("  Strong model (80): oracle=0.8, team=0.85, benefit=0.05")
    print("  Medium model (70): oracle=0.6, team=0.75, benefit=0.15")
    print("  Weak model (60):   oracle=0.4, team=0.7,  benefit=0.30")
    print("  Expected: Higher capability → Lower benefit (inverse scaling)")
    
    # Calculate benefits
    model_benefits = {}
    
    for result in test_data:
        model = result['model']
        if model not in model_benefits:
            model_benefits[model] = {
                'capability': result['capability'],
                'oracle_scores': [],
                'team_scores': []
            }
        
        if result['condition'] == 'oracle-1x':
            model_benefits[model]['oracle_scores'].append(result['score'])
        elif result['condition'] == 'team-standard':
            model_benefits[model]['team_scores'].append(result['score'])
    
    capabilities = []
    benefits = []
    
    print("\nCalculated benefits:")
    for model, data in model_benefits.items():
        oracle_avg = sum(data['oracle_scores']) / len(data['oracle_scores'])
        team_avg = sum(data['team_scores']) / len(data['team_scores'])
        benefit = team_avg - oracle_avg
        
        capabilities.append(data['capability'])
        benefits.append(benefit)
        
        print(f"  {model} (cap={data['capability']}): benefit={benefit:.3f}")
    
    # Calculate correlation manually
    n = len(capabilities)
    sum_x = sum(capabilities)
    sum_y = sum(benefits)
    sum_xy = sum(x * y for x, y in zip(capabilities, benefits))
    sum_x2 = sum(x * x for x in capabilities)
    sum_y2 = sum(y * y for y in benefits)
    
    print(f"\nCorrelation calculation:")
    print(f"  n = {n}")
    print(f"  sum_x = {sum_x}")
    print(f"  sum_y = {sum_y}")
    print(f"  sum_xy = {sum_xy}")
    print(f"  sum_x2 = {sum_x2}")
    print(f"  sum_y2 = {sum_y2}")
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5
    
    print(f"  numerator = {numerator}")
    print(f"  denominator = {denominator}")
    
    if denominator > 0:
        correlation = numerator / denominator
        print(f"  correlation = {correlation:.3f}")
        
        if correlation < 0:
            print("✓ Negative correlation detected (correct for inverse scaling)")
        else:
            print("✗ Positive correlation detected (wrong for inverse scaling)")
    else:
        print("✗ Correlation calculation failed")

def main():
    """Run all debugging tests"""
    
    debug_data_consistency()
    debug_scaling_calculation()

if __name__ == "__main__":
    main()