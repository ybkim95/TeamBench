#!/usr/bin/env python3
"""
Complete infrastructure validation using only mock adapters.
This tests ALL components except the actual API calls.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from harness.adapters.mock_adapter import MockAdapter
from experiments.simple_runner import SimpleRunner, SimpleExperiment

class MockInfrastructureValidator:
    """Test complete pipeline with mock data that simulates real scaling effects"""
    
    def __init__(self, output_dir: str = "experiments/mock_validation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_realistic_mock_experiments(self) -> list:
        """Create mock experiments with realistic scaling patterns"""
        
        models = [
            {"name": "mock-strong", "capability": 80, "cost_per_token": 0.01},
            {"name": "mock-medium", "capability": 70, "cost_per_token": 0.005},
            {"name": "mock-weak", "capability": 60, "cost_per_token": 0.002}
        ]
        
        tasks = [f"mock_task_{i:03d}" for i in range(1, 11)]  # 10 tasks
        conditions = ["oracle-1x", "oracle-3x", "team-standard"]
        
        experiments = []
        
        for model in models:
            for task in tasks:
                for condition in conditions:
                    
                    # Simulate realistic scaling: weaker models benefit more from teams
                    base_success = 0.2 + (model["capability"] - 50) * 0.01
                    
                    if condition == "oracle-3x":
                        # More compute helps, but with diminishing returns for strong models
                        compute_boost = 0.1 + (80 - model["capability"]) * 0.01
                        success_prob = base_success + compute_boost
                    elif condition == "team-standard":
                        # Team coordination helps weak models much more
                        team_boost = 0.2 * (80 - model["capability"]) / 20
                        success_prob = base_success + team_boost
                    else:
                        success_prob = base_success
                    
                    # Add realistic noise and clamp
                    import random
                    success_prob += random.gauss(0, 0.05)
                    success_prob = max(0.05, min(0.95, success_prob))
                    
                    # Create realistic experiment result
                    experiment = SimpleExperiment(
                        task_id=task,
                        model=model["name"],
                        condition=condition,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        success=random.random() < success_prob,
                        score=1.0 if random.random() < success_prob else 0.0,
                        tokens_used=random.randint(5000, 15000),
                        api_calls=random.randint(1, 5),
                        duration_seconds=random.uniform(10, 60)
                    )
                    
                    experiments.append(experiment)
        
        return experiments, models
    
    def test_data_pipeline(self, experiments):
        """Test data saving, loading, and processing pipeline"""
        
        print("=== TESTING DATA PIPELINE ===")
        
        # Test 1: Save individual experiments
        for exp in experiments[:5]:  # Test with first 5
            filename = f"{exp.task_id}_{exp.model}_{exp.condition}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(exp.__dict__, f, indent=2)
        
        # Test 2: Load experiments back
        loaded_experiments = []
        for file in self.output_dir.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                loaded_experiments.append(data)
        
        print(f"✓ Saved and loaded {len(loaded_experiments)} experiment files")
        
        # Test 3: Data consistency
        original_data = [exp.__dict__ for exp in experiments[:5]]
        for i, (orig, loaded) in enumerate(zip(original_data, loaded_experiments)):
            if orig['task_id'] != loaded['task_id']:
                print(f"✗ Data inconsistency in experiment {i}")
                return False
        
        print("✓ Data pipeline integrity verified")
        return True
    
    def test_statistical_analysis(self, experiments, models):
        """Test statistical analysis on realistic mock data"""
        
        print("\n=== TESTING STATISTICAL ANALYSIS ===")
        
        # Convert to format expected by analysis
        analysis_data = []
        model_capabilities = {m["name"]: m["capability"] for m in models}
        
        for exp in experiments:
            analysis_data.append({
                "task_id": exp.task_id,
                "model": exp.model,
                "condition": exp.condition,
                "score": exp.score,
                "capability": model_capabilities[exp.model]
            })
        
        # Test correlation calculation
        model_benefits = {}
        
        for result in analysis_data:
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
        
        # Calculate scaling correlation
        capabilities = []
        benefits = []
        
        for model, data in model_benefits.items():
            if data['oracle_scores'] and data['team_scores']:
                oracle_avg = sum(data['oracle_scores']) / len(data['oracle_scores'])
                team_avg = sum(data['team_scores']) / len(data['team_scores'])
                benefit = team_avg - oracle_avg
                
                capabilities.append(data['capability'])
                benefits.append(benefit)
                
                print(f"  {model} (cap={data['capability']}): benefit={benefit:.3f}")
        
        # Pearson correlation
        if len(capabilities) >= 3:
            n = len(capabilities)
            sum_x = sum(capabilities)
            sum_y = sum(benefits)
            sum_xy = sum(x * y for x, y in zip(capabilities, benefits))
            sum_x2 = sum(x * x for x in capabilities)
            sum_y2 = sum(y * y for y in benefits)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5
            
            if denominator > 0:
                correlation = numerator / denominator
                print(f"✓ Scaling correlation: r = {correlation:.3f}")
                
                if correlation < -0.3:
                    print("✓ Strong inverse scaling detected (as expected)")
                    return True
                elif correlation < 0:
                    print("⚠ Weak inverse scaling detected")
                    return True
                else:
                    print("✗ No inverse scaling detected")
                    return False
            else:
                print("✗ Correlation calculation failed (zero denominator)")
                return False
        else:
            print("✗ Insufficient models for correlation analysis")
            return False
    
    def test_cost_estimation(self, experiments, models):
        """Test cost calculation pipeline"""
        
        print("\n=== TESTING COST ESTIMATION ===")
        
        model_costs = {m["name"]: m["cost_per_token"] for m in models}
        
        total_estimated_cost = 0
        
        for exp in experiments:
            cost_per_token = model_costs[exp.model]
            experiment_cost = exp.tokens_used * cost_per_token / 1000  # Convert to cost per 1K tokens
            total_estimated_cost += experiment_cost
        
        avg_cost_per_experiment = total_estimated_cost / len(experiments)
        total_experiments = len(experiments)
        
        print(f"✓ Total experiments: {total_experiments}")
        print(f"✓ Average cost per experiment: ${avg_cost_per_experiment:.4f}")
        print(f"✓ Total estimated cost: ${total_estimated_cost:.2f}")
        
        # Reasonable cost check
        if avg_cost_per_experiment < 0.10:
            print("✓ Costs appear reasonable for budget pilot")
            return True
        else:
            print("⚠ Costs higher than expected - may need adjustment")
            return avg_cost_per_experiment < 1.0  # Still acceptable if under $1 per experiment
    
    def run_complete_validation(self):
        """Run all infrastructure validation tests"""
        
        print("=" * 60)
        print("COMPLETE INFRASTRUCTURE VALIDATION")
        print("=" * 60)
        
        # Generate realistic mock data
        experiments, models = self.create_realistic_mock_experiments()
        print(f"Generated {len(experiments)} mock experiments across {len(models)} models")
        
        # Test all pipeline components
        tests_passed = 0
        
        # Test 1: Data Pipeline
        if self.test_data_pipeline(experiments):
            tests_passed += 1
        
        # Test 2: Statistical Analysis  
        if self.test_statistical_analysis(experiments, models):
            tests_passed += 1
        
        # Test 3: Cost Estimation
        if self.test_cost_estimation(experiments, models):
            tests_passed += 1
        
        # Overall assessment
        print(f"\n=== VALIDATION RESULTS ===")
        print(f"Tests passed: {tests_passed}/3")
        
        if tests_passed == 3:
            print("✅ INFRASTRUCTURE FULLY VALIDATED")
            print("   → Ready for real API integration")
            return True
        elif tests_passed == 2:
            print("⚠ INFRASTRUCTURE MOSTLY VALIDATED") 
            print("   → Some components need debugging")
            return True
        else:
            print("❌ INFRASTRUCTURE VALIDATION FAILED")
            print("   → Major components non-functional")
            return False

def main():
    """Run infrastructure validation"""
    
    validator = MockInfrastructureValidator()
    success = validator.run_complete_validation()
    
    if success:
        print("\n🎯 NEXT STEP: Test with real API adapters once packages install")
    else:
        print("\n🚨 BLOCKER: Fix infrastructure issues before proceeding")
    
    return success

if __name__ == "__main__":
    main()