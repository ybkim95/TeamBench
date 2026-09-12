#!/usr/bin/env python3
"""
Compute-controlled experiment runner for rigorous scaling analysis.
Ensures fair comparison between team and solo agents by controlling compute budget.
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import numpy as np

from harness.agent_interface import RoleConfig
from harness.agent_loop import AgentLoop
from harness.orchestrator import TaskOrchestrator
from harness.schemas import ModelConfig
from harness.adapters import create_adapter

@dataclass
class ComputeMetrics:
    """Track compute usage for fair comparison"""
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0
    wall_time_seconds: float = 0.0
    thinking_tokens: int = 0  # For o1-style models
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.thinking_tokens
    
    @property
    def normalized_compute(self) -> float:
        """Normalize to single unit of compute (baseline = 1.0)"""
        # Rough approximation: 1K tokens ≈ 1 compute unit
        return self.total_tokens / 1000.0

@dataclass
class ControlledExperiment:
    """Single experiment with compute controls"""
    task_id: str
    model: str
    condition: str
    compute_budget: float  # Relative to baseline
    attempt: int
    timestamp: str
    
    # Results
    success: bool = False
    score: float = 0.0
    compute_used: Optional[ComputeMetrics] = None
    raw_output: Optional[Dict] = None
    error: Optional[str] = None

class ComputeControlledRunner:
    """Run experiments with rigorous compute controls"""
    
    def __init__(self, output_dir: str = "experiments/controlled_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Control conditions with compute budgets
        self.conditions = {
            "oracle-1x": {
                "type": "solo",
                "compute_budget": 1.0,
                "max_tokens": 8192,
                "description": "Single agent, standard budget"
            },
            "oracle-3x": {
                "type": "solo", 
                "compute_budget": 3.0,
                "max_tokens": 24576,
                "description": "Single agent, 3x token budget"
            },
            "oracle-retry-3": {
                "type": "solo_retry",
                "compute_budget": 3.0,
                "max_tokens": 8192,
                "retries": 3,
                "description": "Single agent, best of 3 attempts"
            },
            "oracle-cot": {
                "type": "solo",
                "compute_budget": 2.0,
                "max_tokens": 16384,
                "cot_prompt": True,
                "description": "Single agent with chain-of-thought"
            },
            "team-standard": {
                "type": "team",
                "compute_budget": 3.0,
                "max_tokens": 8192,  # Per agent
                "description": "Standard 3-agent team"
            },
            "team-budget-matched": {
                "type": "team",
                "compute_budget": 1.0,
                "max_tokens": 2730,  # 8192/3
                "description": "Team with 1/3 budget per agent"
            },
            "team-no-verify": {
                "type": "team_partial",
                "compute_budget": 2.0,
                "max_tokens": 4096,  # Per agent
                "skip_verifier": True,
                "description": "Planner + Executor only"
            }
        }
        
        self.cot_prompt = """
Before starting, think step-by-step about:
1. What the task is asking for
2. What information you have access to
3. Your approach to solving it
4. Potential challenges

Then proceed with the implementation.
"""
        
    async def run_controlled_experiment(
        self, 
        task_path: Path,
        model_config: ModelConfig,
        condition: str
    ) -> ControlledExperiment:
        """Run a single controlled experiment"""
        
        if condition not in self.conditions:
            raise ValueError(f"Unknown condition: {condition}")
        
        config = self.conditions[condition]
        start_time = time.time()
        
        experiment = ControlledExperiment(
            task_id=task_path.name,
            model=model_config.name,
            condition=condition,
            compute_budget=config["compute_budget"],
            attempt=1,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        try:
            if config["type"] == "solo":
                result = await self._run_solo(
                    task_path, model_config, config
                )
            elif config["type"] == "solo_retry":
                result = await self._run_solo_retry(
                    task_path, model_config, config
                )
            elif config["type"] == "team":
                result = await self._run_team(
                    task_path, model_config, config
                )
            elif config["type"] == "team_partial":
                result = await self._run_team_partial(
                    task_path, model_config, config
                )
            else:
                raise ValueError(f"Unknown condition type: {config['type']}")
            
            experiment.success = result["success"]
            experiment.score = result["score"]
            experiment.compute_used = result["compute"]
            experiment.raw_output = result
            
        except Exception as e:
            experiment.error = str(e)
            experiment.success = False
            experiment.score = 0.0
        
        experiment.compute_used.wall_time_seconds = time.time() - start_time
        
        # Save result immediately
        self._save_experiment(experiment)
        
        return experiment
    
    async def _run_solo(
        self, 
        task_path: Path,
        model_config: ModelConfig,
        config: Dict
    ) -> Dict:
        """Run single agent with specified compute budget"""
        
        # Configure agent with token limits
        agent_config = RoleConfig(
            role="oracle",
            model=model_config,
            tools=["bash", "write", "read"],
            max_tokens=config["max_tokens"]
        )
        
        # Add CoT prompt if specified
        if config.get("cot_prompt"):
            agent_config.system_prompt = self.cot_prompt + "\n" + agent_config.system_prompt
        
        # Run agent
        loop = AgentLoop(agent_config, task_path / "workspace")
        
        # Read full task specification
        with open(task_path / "spec.md") as f:
            task_spec = f.read()
        
        result = await loop.run(task_spec, max_turns=30)
        
        # Compute metrics
        compute = ComputeMetrics(
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            api_calls=result.get("api_calls", 0),
            thinking_tokens=result.get("thinking_tokens", 0)
        )
        
        # Check success
        success = self._check_success(task_path, result)
        
        return {
            "success": success,
            "score": 1.0 if success else 0.0,
            "compute": compute,
            "turns": result.get("turns", 0),
            "output": result
        }
    
    async def _run_solo_retry(
        self,
        task_path: Path,
        model_config: ModelConfig,
        config: Dict
    ) -> Dict:
        """Run single agent with retries, taking best result"""
        
        results = []
        total_compute = ComputeMetrics()
        
        for attempt in range(config["retries"]):
            result = await self._run_solo(task_path, model_config, {
                **config,
                "type": "solo"  # Prevent recursion
            })
            
            results.append(result)
            
            # Accumulate compute
            total_compute.input_tokens += result["compute"].input_tokens
            total_compute.output_tokens += result["compute"].output_tokens
            total_compute.api_calls += result["compute"].api_calls
            
            # Early exit if successful
            if result["success"]:
                break
        
        # Return best result with total compute
        best_result = max(results, key=lambda r: r["score"])
        best_result["compute"] = total_compute
        best_result["attempts"] = len(results)
        
        return best_result
    
    async def _run_team(
        self,
        task_path: Path,
        model_config: ModelConfig,
        config: Dict
    ) -> Dict:
        """Run full team with specified compute budget"""
        
        # Configure team members with budget constraints
        planner_config = RoleConfig(
            role="planner",
            model=model_config,
            tools=["send_message"],
            max_tokens=config["max_tokens"]
        )
        
        executor_config = RoleConfig(
            role="executor",
            model=model_config,
            tools=["bash", "write", "read", "send_message"],
            max_tokens=config["max_tokens"]
        )
        
        verifier_config = RoleConfig(
            role="verifier",
            model=model_config,
            tools=["write_attestation"],
            max_tokens=config["max_tokens"]
        )
        
        # Run orchestration
        result = run_orchestration(
            task_path=task_path,
            planner_config=planner_config,
            executor_config=executor_config,
            verifier_config=verifier_config,
            max_remediation_loops=2
        )
        
        # Extract compute metrics
        compute = ComputeMetrics()
        for phase in result.phases:
            for turn in phase.turns:
                compute.input_tokens += turn.get("input_tokens", 0)
                compute.output_tokens += turn.get("output_tokens", 0)
                compute.api_calls += 1
        
        return {
            "success": result.verdict == "pass",
            "score": 1.0 if result.verdict == "pass" else 0.0,
            "compute": compute,
            "phases": len(result.phases),
            "total_turns": result.total_turns,
            "output": asdict(result)
        }
    
    async def _run_team_partial(
        self,
        task_path: Path,
        model_config: ModelConfig,
        config: Dict
    ) -> Dict:
        """Run partial team (e.g., no verifier)"""
        
        if config.get("skip_verifier"):
            # Run Planner + Executor only
            planner_config = RoleConfig(
                role="planner",
                model=model_config,
                tools=["send_message"],
                max_tokens=config["max_tokens"]
            )
            
            executor_config = RoleConfig(
                role="executor",
                model=model_config,
                tools=["bash", "write", "read", "send_message"],
                max_tokens=config["max_tokens"]
            )
            
            # Run without verifier
            result = run_orchestration(
                task_path=task_path,
                planner_config=planner_config,
                executor_config=executor_config,
                verifier_config=None,  # No verifier
                max_remediation_loops=0
            )
        else:
            raise NotImplementedError(f"Partial team config not implemented")
        
        # Extract metrics (similar to full team)
        compute = ComputeMetrics()
        for phase in result.phases:
            for turn in phase.turns:
                compute.input_tokens += turn.get("input_tokens", 0)
                compute.output_tokens += turn.get("output_tokens", 0)
                compute.api_calls += 1
        
        return {
            "success": self._check_success_no_verifier(task_path),
            "score": 1.0 if self._check_success_no_verifier(task_path) else 0.0,
            "compute": compute,
            "output": asdict(result)
        }
    
    def _check_success(self, task_path: Path, result: Dict) -> bool:
        """Check if task was successfully completed"""
        
        # Run grading script
        grade_script = task_path / "grade.sh"
        if not grade_script.exists():
            return False
        
        import subprocess
        try:
            output = subprocess.run(
                ["bash", str(grade_script), str(task_path / "workspace"), "/tmp/attestation.json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return output.returncode == 0
        except:
            return False
    
    def _check_success_no_verifier(self, task_path: Path) -> bool:
        """Check success without verifier attestation"""
        # For no-verifier condition, check workspace directly
        return self._check_success(task_path, {})
    
    def _save_experiment(self, experiment: ControlledExperiment):
        """Save experiment result to disk"""
        
        # Create unique filename
        filename = f"{experiment.task_id}_{experiment.model}_{experiment.condition}_{experiment.attempt}.json"
        filepath = self.output_dir / filename
        
        # Convert to dict
        exp_dict = asdict(experiment)
        if experiment.compute_used:
            exp_dict["compute_used"] = asdict(experiment.compute_used)
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(exp_dict, f, indent=2, default=str)
    
    async def run_scaling_experiments(
        self,
        models: List[ModelConfig],
        tasks: List[Path],
        conditions: Optional[List[str]] = None
    ) -> Dict:
        """Run full scaling experiment suite"""
        
        if conditions is None:
            conditions = list(self.conditions.keys())
        
        results = []
        total_experiments = len(models) * len(tasks) * len(conditions)
        completed = 0
        
        print(f"Starting {total_experiments} experiments...")
        
        for model in models:
            for task in tasks:
                for condition in conditions:
                    print(f"[{completed+1}/{total_experiments}] {model.name} on {task.name} ({condition})")
                    
                    experiment = await self.run_controlled_experiment(
                        task, model, condition
                    )
                    results.append(experiment)
                    completed += 1
                    
                    # Save checkpoint
                    if completed % 10 == 0:
                        self._save_checkpoint(results)
        
        # Final save
        self._save_checkpoint(results)
        
        return self._analyze_results(results)
    
    def _save_checkpoint(self, results: List[ControlledExperiment]):
        """Save intermediate results"""
        
        checkpoint_file = self.output_dir / "checkpoint.json"
        
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "n_experiments": len(results),
            "results": [asdict(r) for r in results]
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _analyze_results(self, results: List[ControlledExperiment]) -> Dict:
        """Analyze results for scaling patterns"""
        
        # Group by model
        by_model = {}
        for r in results:
            if r.model not in by_model:
                by_model[r.model] = []
            by_model[r.model].append(r)
        
        analysis = {
            "summary": {},
            "scaling": {},
            "compute_efficiency": {}
        }
        
        # Compute summary statistics per model per condition
        for model, experiments in by_model.items():
            model_stats = {}
            
            for condition in self.conditions:
                condition_exps = [e for e in experiments if e.condition == condition]
                if condition_exps:
                    model_stats[condition] = {
                        "success_rate": np.mean([e.success for e in condition_exps]),
                        "avg_score": np.mean([e.score for e in condition_exps]),
                        "avg_compute": np.mean([e.compute_used.normalized_compute 
                                               for e in condition_exps if e.compute_used]),
                        "n": len(condition_exps)
                    }
            
            analysis["summary"][model] = model_stats
        
        # Calculate team benefit controlling for compute
        for model in by_model:
            if "oracle-1x" in analysis["summary"][model] and "team-standard" in analysis["summary"][model]:
                oracle_score = analysis["summary"][model]["oracle-1x"]["avg_score"]
                team_score = analysis["summary"][model]["team-standard"]["avg_score"]
                
                # Compute-controlled comparison
                if "oracle-3x" in analysis["summary"][model]:
                    oracle_3x_score = analysis["summary"][model]["oracle-3x"]["avg_score"]
                    
                    # True team benefit = team performance - compute-matched oracle
                    true_team_benefit = team_score - oracle_3x_score
                    
                    analysis["scaling"][model] = {
                        "raw_team_benefit": team_score - oracle_score,
                        "compute_controlled_benefit": true_team_benefit,
                        "compute_explains": (oracle_3x_score - oracle_score) / max(team_score - oracle_score, 0.01)
                    }
        
        return analysis

def main():
    """Example usage"""
    import asyncio
    
    runner = ComputeControlledRunner()
    
    # Define test models
    models = [
        ModelConfig(name="gpt-4o-mini", provider="openai"),
        ModelConfig(name="claude-3-haiku", provider="anthropic"),
    ]
    
    # Get test tasks
    tasks = list(Path("tasks").glob("EASY*"))[:5]
    
    # Run controlled experiments
    results = asyncio.run(runner.run_scaling_experiments(
        models=models,
        tasks=tasks,
        conditions=["oracle-1x", "oracle-3x", "team-standard"]
    ))
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()