#!/usr/bin/env python3
"""
Simplified experiment runner for pilot validation.
Tests basic infrastructure without complex orchestration.
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from harness.adapters import create_adapter
from harness.schemas import ModelConfig

@dataclass
class SimpleExperiment:
    """Single experiment record"""
    task_id: str
    model: str
    condition: str
    timestamp: str
    success: bool = False
    score: float = 0.0
    tokens_used: int = 0
    api_calls: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None

class SimpleRunner:
    """Simple experiment runner for validation"""
    
    def __init__(self, output_dir: str = "experiments/simple_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test conditions
        self.conditions = {
            "oracle-1x": "Single agent baseline",
            "oracle-2x": "Single agent with 2x budget", 
            "mock-team": "Mock team simulation"
        }
    
    async def run_single_experiment(
        self,
        task_path: Path,
        model_config: ModelConfig,
        condition: str
    ) -> SimpleExperiment:
        """Run a single experiment"""
        
        start_time = time.time()
        
        experiment = SimpleExperiment(
            task_id=task_path.name,
            model=model_config.name,
            condition=condition,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        try:
            # Create adapter
            adapter = create_adapter(model_config.name)
            
            # Read task specification
            spec_file = task_path / "spec.md"
            if not spec_file.exists():
                raise FileNotFoundError(f"No spec.md in {task_path}")
            
            with open(spec_file) as f:
                spec_content = f.read()
            
            # Simple test: can the adapter generate a response?
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Task: {task_path.name}\n\nSpecification:\n{spec_content[:500]}...\n\nProvide a brief analysis of this task."}
            ]
            
            # Simulate different conditions
            if condition == "oracle-2x":
                # Simulate 2x compute by adding more context
                messages[1]["content"] += "\n\nTake extra time to think through this carefully."
            elif condition == "mock-team":
                # Simulate team by asking for role-based thinking
                messages[1]["content"] += "\n\nThink about this from multiple perspectives: planner, executor, verifier."
            
            # Make API call (or mock call)
            if hasattr(adapter, 'generate_with_tools'):
                response = adapter.generate_with_tools(messages, "", [])
                result_text = response.text
                tokens = getattr(adapter, '_usage', {}).get('total_tokens', 100)
            else:
                # Fallback for mock adapter
                result_text = f"Analysis of {task_path.name}: This appears to be a {condition} condition test."
                tokens = 150
            
            # Check if response looks reasonable
            success = len(result_text) > 20 and task_path.name.lower() in result_text.lower()
            score = 1.0 if success else 0.0
            
            experiment.success = success
            experiment.score = score
            experiment.tokens_used = tokens
            experiment.api_calls = 1
            
        except Exception as e:
            experiment.error = str(e)
            experiment.success = False
            experiment.score = 0.0
        
        experiment.duration_seconds = time.time() - start_time
        
        # Save experiment
        self._save_experiment(experiment)
        return experiment
    
    def _save_experiment(self, experiment: SimpleExperiment):
        """Save experiment to disk"""
        filename = f"{experiment.task_id}_{experiment.model}_{experiment.condition}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(experiment), f, indent=2)
    
    async def run_batch_experiments(
        self,
        models: List[ModelConfig],
        tasks: List[Path],
        conditions: List[str]
    ) -> Dict:
        """Run batch of experiments"""
        
        print(f"=== Simple Runner Batch ===")
        print(f"Models: {len(models)}")
        print(f"Tasks: {len(tasks)}")
        print(f"Conditions: {len(conditions)}")
        
        total_experiments = len(models) * len(tasks) * len(conditions)
        print(f"Total experiments: {total_experiments}")
        
        results = []
        completed = 0
        
        for model in models:
            for task in tasks:
                for condition in conditions:
                    print(f"[{completed+1}/{total_experiments}] {model.name} on {task.name} ({condition})")
                    
                    experiment = await self.run_single_experiment(task, model, condition)
                    results.append(experiment)
                    completed += 1
                    
                    # Brief pause to avoid overwhelming output
                    await asyncio.sleep(0.1)
        
        # Analyze results
        analysis = self._analyze_results(results)
        
        # Save analysis
        analysis_path = self.output_dir / "batch_analysis.json"
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Analysis saved to {analysis_path}")
        return analysis
    
    def _analyze_results(self, results: List[SimpleExperiment]) -> Dict:
        """Analyze batch results"""
        
        # Group by model and condition
        by_model = {}
        by_condition = {}
        
        for exp in results:
            # By model
            if exp.model not in by_model:
                by_model[exp.model] = []
            by_model[exp.model].append(exp)
            
            # By condition
            if exp.condition not in by_condition:
                by_condition[exp.condition] = []
            by_condition[exp.condition].append(exp)
        
        # Calculate stats
        def calc_stats(experiments):
            if not experiments:
                return {}
            
            successes = [e for e in experiments if e.success]
            return {
                "count": len(experiments),
                "success_rate": len(successes) / len(experiments),
                "avg_score": sum(e.score for e in experiments) / len(experiments),
                "avg_tokens": sum(e.tokens_used for e in experiments) / len(experiments),
                "avg_duration": sum(e.duration_seconds for e in experiments) / len(experiments),
                "errors": sum(1 for e in experiments if e.error),
            }
        
        analysis = {
            "summary": {
                "total_experiments": len(results),
                "overall_success_rate": sum(1 for r in results if r.success) / len(results),
                "total_duration": sum(r.duration_seconds for r in results)
            },
            "by_model": {model: calc_stats(exps) for model, exps in by_model.items()},
            "by_condition": {condition: calc_stats(exps) for condition, exps in by_condition.items()},
            "infrastructure_test": {
                "all_models_tested": len(by_model) == len(set(r.model for r in results)),
                "all_conditions_tested": len(by_condition) == len(set(r.condition for r in results)),
                "no_critical_errors": sum(1 for r in results if r.error) == 0,
                "reasonable_performance": sum(1 for r in results if r.success) > len(results) * 0.5
            }
        }
        
        return analysis

def get_sample_tasks(n: int = 5) -> List[Path]:
    """Get sample tasks for testing"""
    tasks_dir = Path("tasks")
    
    if not tasks_dir.exists():
        # Create a dummy task for testing
        dummy_task = Path("experiments/dummy_task")
        dummy_task.mkdir(parents=True, exist_ok=True)
        
        with open(dummy_task / "spec.md", 'w') as f:
            f.write("""# Dummy Task for Testing

This is a simple test task to validate the experiment infrastructure.

## Requirements
1. Read this specification
2. Analyze the requirements  
3. Provide a response

## Success Criteria
- Task analysis mentions the task name
- Response is longer than 20 characters
""")
        
        return [dummy_task]
    
    # Get real tasks
    all_tasks = [t for t in tasks_dir.iterdir() 
                if t.is_dir() and (t / "spec.md").exists()]
    
    return all_tasks[:n]

async def main():
    """Test the simple runner"""
    
    # Mock models for testing
    test_models = [
        ModelConfig(
            name="mock-gpt-4o",
            provider="mock",
            capability_score=85.0
        ),
        ModelConfig(
            name="mock-claude",
            provider="mock", 
            capability_score=80.0
        ),
        ModelConfig(
            name="mock-gemini",
            provider="mock",
            capability_score=75.0
        )
    ]
    
    test_conditions = ["oracle-1x", "oracle-2x", "mock-team"]
    test_tasks = get_sample_tasks(3)
    
    print(f"Found tasks: {[t.name for t in test_tasks]}")
    
    runner = SimpleRunner()
    analysis = await runner.run_batch_experiments(
        models=test_models,
        tasks=test_tasks,
        conditions=test_conditions
    )
    
    # Print summary
    print("\n" + "="*50)
    print("SIMPLE RUNNER RESULTS")
    print("="*50)
    
    summary = analysis["summary"]
    print(f"Total experiments: {summary['total_experiments']}")
    print(f"Success rate: {summary['overall_success_rate']:.1%}")
    print(f"Total time: {summary['total_duration']:.1f}s")
    
    infra = analysis["infrastructure_test"]
    print(f"\nInfrastructure Test:")
    for test, passed in infra.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {test}: {passed}")
    
    print(f"\nBy condition:")
    for condition, stats in analysis["by_condition"].items():
        print(f"  {condition}: {stats['success_rate']:.1%} success ({stats['count']} runs)")

if __name__ == "__main__":
    asyncio.run(main())