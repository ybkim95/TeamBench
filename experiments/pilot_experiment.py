#!/usr/bin/env python3
"""
Pilot experiment for validating compute-controlled methodology.
Runs 10 tasks × 3 models × 3 conditions = 90 experiments.
"""

import asyncio
import json
from pathlib import Path
from typing import List
import time
from datetime import datetime, timezone

from experiments.model_configs import MODEL_CONFIGS, get_available_models
from harness.compute_controlled_runner import ComputeControlledRunner
from harness.schemas import ModelConfig

# For pilot, use mock models to validate infrastructure
PILOT_MODELS = [
    ModelConfig(
        name="mock-gpt-4o",
        provider="mock",
        capability_score=85.0,
        cost_per_1k_input=5.0,
        cost_per_1k_output=15.0,
        max_context=128000,
        supports_tools=True
    ),
    ModelConfig(
        name="mock-claude-sonnet",
        provider="mock", 
        capability_score=79.0,
        cost_per_1k_input=3.0,
        cost_per_1k_output=15.0,
        max_context=200000,
        supports_tools=True
    ),
    ModelConfig(
        name="mock-gpt-4o-mini",
        provider="mock",
        capability_score=76.0,
        cost_per_1k_input=0.15,
        cost_per_1k_output=0.60,
        max_context=128000,
        supports_tools=True
    )
]

# Conditions to test in pilot
PILOT_CONDITIONS = [
    "oracle-1x",      # Baseline single agent
    "oracle-3x",      # Compute control (3x tokens)
    "team-standard"   # Full team
]

class PilotExperiment:
    """Run pilot experiments to validate methodology"""
    
    def __init__(self, output_dir: str = "experiments/pilot_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runner = ComputeControlledRunner(str(self.output_dir))
        
    def get_pilot_tasks(self, n_tasks: int = 10) -> List[Path]:
        """Get subset of tasks for pilot"""
        
        # Look for existing easy tasks
        tasks_dir = Path("tasks")
        easy_tasks = list(tasks_dir.glob("EASY*"))
        
        if len(easy_tasks) >= n_tasks:
            return easy_tasks[:n_tasks]
        
        # If not enough easy tasks, use any available tasks
        all_tasks = [t for t in tasks_dir.iterdir() if t.is_dir() and (t / "spec.md").exists()]
        return all_tasks[:n_tasks]
    
    async def run_pilot(self) -> dict:
        """Run the pilot experiment"""
        
        print("=== TeamBench Pilot Experiment ===")
        print(f"Start time: {datetime.now()}")
        
        # Get tasks
        tasks = self.get_pilot_tasks()
        print(f"Selected {len(tasks)} tasks: {[t.name for t in tasks]}")
        
        if len(tasks) == 0:
            raise ValueError("No tasks found! Please ensure tasks directory exists with spec.md files.")
        
        # Run experiments
        print(f"\nRunning {len(PILOT_MODELS)} models × {len(tasks)} tasks × {len(PILOT_CONDITIONS)} conditions")
        print(f"Total experiments: {len(PILOT_MODELS) * len(tasks) * len(PILOT_CONDITIONS)}")
        
        start_time = time.time()
        results = await self.runner.run_scaling_experiments(
            models=PILOT_MODELS,
            tasks=tasks,
            conditions=PILOT_CONDITIONS
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nPilot completed in {duration:.1f} seconds")
        
        # Analyze results
        analysis = self._analyze_pilot_results(results)
        
        # Save analysis
        report_path = self.output_dir / "pilot_analysis.json"
        with open(report_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Pilot analysis saved to {report_path}")
        return analysis
    
    def _analyze_pilot_results(self, results: dict) -> dict:
        """Analyze pilot results for methodology validation"""
        
        analysis = {
            "metadata": {
                "experiment_type": "pilot",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "models": [m.name for m in PILOT_MODELS],
                "conditions": PILOT_CONDITIONS
            },
            "infrastructure_validation": {},
            "scaling_indicators": {},
            "variance_analysis": {},
            "next_steps": {}
        }
        
        # Check infrastructure worked
        summary = results.get("summary", {})
        total_conditions = sum(
            len(model_stats) for model_stats in summary.values()
        )
        
        analysis["infrastructure_validation"] = {
            "total_experiments_run": total_conditions,
            "all_conditions_tested": all(
                condition in model_stats 
                for model_stats in summary.values() 
                for condition in PILOT_CONDITIONS
            ),
            "compute_tracking_working": all(
                "avg_compute" in model_stats.get(condition, {})
                for model_stats in summary.values()
                for condition in PILOT_CONDITIONS
            )
        }
        
        # Look for scaling signals
        scaling_data = results.get("scaling", {})
        if scaling_data:
            analysis["scaling_indicators"] = {
                "models_with_benefit_data": len(scaling_data),
                "compute_controls_available": any(
                    "compute_controlled_benefit" in model_data
                    for model_data in scaling_data.values()
                ),
                "sample_benefit_values": {
                    model: data.get("compute_controlled_benefit", 0)
                    for model, data in list(scaling_data.items())[:3]
                }
            }
        
        # Variance analysis
        variance_stats = []
        for model_name, model_stats in summary.items():
            for condition, stats in model_stats.items():
                if "n" in stats and stats["n"] > 0:
                    # Estimate variance from available data
                    success_rate = stats.get("avg_score", 0)
                    n = stats["n"]
                    # Binomial variance approximation
                    variance = success_rate * (1 - success_rate) / n if n > 0 else 1.0
                    variance_stats.append({
                        "model": model_name,
                        "condition": condition,
                        "mean": success_rate,
                        "estimated_variance": variance,
                        "n": n
                    })
        
        analysis["variance_analysis"] = {
            "condition_variances": variance_stats,
            "high_variance_conditions": [
                v for v in variance_stats if v["estimated_variance"] > 0.1
            ],
            "sample_size_adequate": all(v["n"] >= 3 for v in variance_stats)
        }
        
        # Recommendations
        infrastructure_ok = analysis["infrastructure_validation"]["all_conditions_tested"]
        has_scaling_data = len(analysis["scaling_indicators"]) > 0
        
        if infrastructure_ok and has_scaling_data:
            recommendation = "PROCEED_TO_MAIN"
            message = "Infrastructure validated. Ready for main experiments."
        elif infrastructure_ok:
            recommendation = "FIX_SCALING_ANALYSIS"
            message = "Infrastructure works but scaling analysis needs debugging."
        else:
            recommendation = "FIX_INFRASTRUCTURE"
            message = "Infrastructure issues detected. Fix before main experiments."
        
        analysis["next_steps"] = {
            "recommendation": recommendation,
            "message": message,
            "estimated_main_experiment_time": "96 hours",
            "estimated_cost": "$2,500 (with real APIs)"
        }
        
        return analysis

def print_pilot_summary(analysis: dict):
    """Print human-readable pilot summary"""
    
    print("\n" + "="*60)
    print("PILOT EXPERIMENT SUMMARY")
    print("="*60)
    
    # Infrastructure
    infra = analysis["infrastructure_validation"]
    print(f"\n🔧 Infrastructure Validation:")
    print(f"  ✓ Total experiments: {infra['total_experiments_run']}")
    print(f"  ✓ All conditions tested: {infra['all_conditions_tested']}")
    print(f"  ✓ Compute tracking: {infra['compute_tracking_working']}")
    
    # Scaling
    scaling = analysis["scaling_indicators"]
    if scaling:
        print(f"\n📊 Scaling Analysis:")
        print(f"  Models with data: {scaling['models_with_benefit_data']}")
        print(f"  Compute controls: {scaling['compute_controls_available']}")
        
        if "sample_benefit_values" in scaling:
            print(f"  Sample benefits:")
            for model, benefit in scaling["sample_benefit_values"].items():
                print(f"    {model}: {benefit:.3f}")
    
    # Variance
    variance = analysis["variance_analysis"]
    print(f"\n📈 Variance Analysis:")
    print(f"  High variance conditions: {len(variance['high_variance_conditions'])}")
    print(f"  Sample size adequate: {variance['sample_size_adequate']}")
    
    # Next steps
    next_steps = analysis["next_steps"]
    print(f"\n🎯 Recommendation: {next_steps['recommendation']}")
    print(f"  {next_steps['message']}")
    print(f"  Main experiment time: {next_steps['estimated_main_experiment_time']}")
    print(f"  Estimated cost: {next_steps['estimated_cost']}")

async def main():
    """Run pilot experiment"""
    
    pilot = PilotExperiment()
    
    try:
        analysis = await pilot.run_pilot()
        print_pilot_summary(analysis)
        
        # Save summary
        with open("experiments/pilot_summary.txt", "w") as f:
            # Redirect print to file
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            print_pilot_summary(analysis)
            sys.stdout = original_stdout
        
        print(f"\nPilot summary saved to experiments/pilot_summary.txt")
        
    except Exception as e:
        print(f"Pilot experiment failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())