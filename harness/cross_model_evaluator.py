"""
Cross-Model Team Composition Evaluator for TeamBench
Tests different model combinations (e.g., Claude Planner + GPT Executor + Gemini Verifier)
"""

import json
import itertools
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from harness.agent_interface import RoleConfig
from harness.orchestrator import OrchestratorResult, run_orchestration
from harness.schemas import ModelConfig

@dataclass
class TeamComposition:
    """Defines a specific model combination for a team"""
    planner_model: ModelConfig
    executor_model: ModelConfig  
    verifier_model: ModelConfig
    composition_id: str = ""
    
    def __post_init__(self):
        if not self.composition_id:
            # Generate unique ID from model combination
            self.composition_id = f"{self.planner_model.name[:3]}-{self.executor_model.name[:3]}-{self.verifier_model.name[:3]}"

@dataclass
class CompositionResult:
    """Results for a specific team composition"""
    composition: TeamComposition
    task_id: str
    success: bool
    score: float
    turns_used: int
    time_seconds: float
    cost_dollars: float
    synergy_score: float  # How well the models work together
    
@dataclass
class CrossModelAnalysis:
    """Analysis of cross-model team performance"""
    best_composition: TeamComposition
    worst_composition: TeamComposition
    all_results: List[CompositionResult]
    synergy_matrix: Dict[str, float]  # Pairwise model synergies
    model_strengths: Dict[str, Dict[str, float]]  # Each model's role performance

class CrossModelEvaluator:
    """Evaluates different model combinations in team settings"""
    
    def __init__(self, models: List[ModelConfig], tasks_dir: str, results_dir: str):
        self.models = models
        self.tasks_dir = Path(tasks_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        # Cost estimates per 1K tokens (approximate)
        self.model_costs = {
            "gpt-4": 0.03,
            "gpt-4o": 0.015,
            "gpt-5": 0.05,
            "claude-3-opus": 0.075,
            "claude-3-sonnet": 0.018,
            "claude-3-haiku": 0.0025,
            "gemini-pro": 0.00125,
            "gemini-ultra": 0.02,
            "llama-3": 0.0001,  # Open source (compute cost)
            "mixtral": 0.0002,
            "qwen": 0.00015
        }
        
    def generate_compositions(self, strategy: str = "all") -> List[TeamComposition]:
        """Generate team compositions based on strategy"""
        
        if strategy == "all":
            # All possible combinations (can be large)
            compositions = []
            for planner, executor, verifier in itertools.product(self.models, repeat=3):
                compositions.append(TeamComposition(planner, executor, verifier))
            return compositions
            
        elif strategy == "diverse":
            # Each role from different provider
            compositions = []
            providers = {}
            for model in self.models:
                provider = model.name.split("-")[0]  # e.g., "gpt", "claude", "gemini"
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(model)
            
            # One model from each provider for each role
            provider_list = list(providers.keys())
            for perm in itertools.permutations(provider_list[:3]):  # Max 3 providers
                if len(perm) >= 3:
                    planner = providers[perm[0]][0]
                    executor = providers[perm[1]][0]
                    verifier = providers[perm[2]][0]
                    compositions.append(TeamComposition(planner, executor, verifier))
            
            return compositions
            
        elif strategy == "optimal":
            # Based on known model strengths
            compositions = []
            
            # Best planner (reasoning)
            planners = [m for m in self.models if "opus" in m.name or "gpt-4" in m.name]
            
            # Best executor (code generation)
            executors = [m for m in self.models if "sonnet" in m.name or "gpt-4o" in m.name]
            
            # Best verifier (attention to detail)
            verifiers = [m for m in self.models if "haiku" in m.name or "gemini" in m.name]
            
            for p in planners[:2]:
                for e in executors[:2]:
                    for v in verifiers[:2]:
                        compositions.append(TeamComposition(p, e, v))
            
            return compositions
            
        elif strategy == "economical":
            # Optimize for cost/performance
            compositions = []
            
            # Expensive planner (most important role)
            expensive = sorted(self.models, key=lambda m: self.model_costs.get(m.name, 0.01), reverse=True)
            
            # Cheap executor and verifier
            cheap = sorted(self.models, key=lambda m: self.model_costs.get(m.name, 0.01))
            
            for p in expensive[:2]:
                for e in cheap[:2]:
                    for v in cheap[:2]:
                        compositions.append(TeamComposition(p, e, v))
            
            return compositions
            
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def evaluate_composition(self, composition: TeamComposition, task_path: Path) -> CompositionResult:
        """Evaluate a single team composition on a task"""
        
        start_time = datetime.now(timezone.utc)
        
        # Configure models for each role
        planner_config = RoleConfig(
            role="planner",
            model=composition.planner_model,
            tools=["send_message"]
        )
        
        executor_config = RoleConfig(
            role="executor",
            model=composition.executor_model,
            tools=["bash", "write", "read", "send_message"]
        )
        
        verifier_config = RoleConfig(
            role="verifier",
            model=composition.verifier_model,
            tools=["write_attestation"]
        )
        
        # Run orchestration
        result = run_orchestration(
            task_path=task_path,
            planner_config=planner_config,
            executor_config=executor_config,
            verifier_config=verifier_config,
            max_remediation_loops=2
        )
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Calculate costs
        total_tokens = result.total_turns * 2000  # Rough estimate
        planner_cost = (total_tokens / 3000) * self.model_costs.get(composition.planner_model.name, 0.01)
        executor_cost = (total_tokens / 3000) * self.model_costs.get(composition.executor_model.name, 0.01)
        verifier_cost = (total_tokens / 3000) * self.model_costs.get(composition.verifier_model.name, 0.01)
        total_cost = planner_cost + executor_cost + verifier_cost
        
        # Calculate synergy score (how well models work together)
        synergy = self._calculate_synergy(composition, result)
        
        return CompositionResult(
            composition=composition,
            task_id=task_path.name,
            success=result.verdict == "pass",
            score=1.0 if result.verdict == "pass" else 0.0,
            turns_used=result.total_turns,
            time_seconds=duration,
            cost_dollars=total_cost,
            synergy_score=synergy
        )
    
    def _calculate_synergy(self, composition: TeamComposition, result: OrchestratorResult) -> float:
        """Calculate how well models work together"""
        
        synergy_factors = []
        
        # Factor 1: Turn efficiency (fewer turns = better synergy)
        expected_turns = 10  # Baseline expectation
        efficiency = expected_turns / max(result.total_turns, 1)
        synergy_factors.append(min(2.0, efficiency))  # Cap at 2x
        
        # Factor 2: Remediation loops (fewer = better)
        remediation_penalty = 1.0 - (result.remediation_loops * 0.25)
        synergy_factors.append(max(0, remediation_penalty))
        
        # Factor 3: Message passing efficiency
        message_ratio = self._analyze_message_patterns(result)
        synergy_factors.append(message_ratio)
        
        # Factor 4: Model compatibility (same family = bonus)
        compatibility = self._check_model_compatibility(composition)
        synergy_factors.append(compatibility)
        
        return np.mean(synergy_factors)
    
    def _analyze_message_patterns(self, result: OrchestratorResult) -> float:
        """Analyze communication patterns between agents"""
        
        total_messages = 0
        useful_messages = 0
        
        for phase in result.phases:
            for turn in phase.turns:
                for tool_call in turn.tool_calls:
                    if tool_call.get("name") == "send_message":
                        total_messages += 1
                        # Check if message led to action (simplified)
                        if phase.success:
                            useful_messages += 1
        
        if total_messages == 0:
            return 0.5  # No messages = neutral score
        
        return useful_messages / total_messages
    
    def _check_model_compatibility(self, composition: TeamComposition) -> float:
        """Check if models are from compatible families"""
        
        def get_family(model_name: str) -> str:
            if "gpt" in model_name:
                return "openai"
            elif "claude" in model_name:
                return "anthropic"
            elif "gemini" in model_name:
                return "google"
            else:
                return "other"
        
        families = [
            get_family(composition.planner_model.name),
            get_family(composition.executor_model.name),
            get_family(composition.verifier_model.name)
        ]
        
        # All same family = high compatibility
        if len(set(families)) == 1:
            return 1.2
        # All different = interesting diversity
        elif len(set(families)) == 3:
            return 1.0
        # Mixed = neutral
        else:
            return 0.9
    
    def run_evaluation(self, task_ids: List[str], strategy: str = "diverse", 
                       parallel: bool = True, max_workers: int = 4) -> CrossModelAnalysis:
        """Run full cross-model evaluation"""
        
        compositions = self.generate_compositions(strategy)
        all_results = []
        
        print(f"Evaluating {len(compositions)} team compositions on {len(task_ids)} tasks")
        
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for comp in compositions:
                    for task_id in task_ids:
                        task_path = self.tasks_dir / task_id
                        if task_path.exists():
                            future = executor.submit(self.evaluate_composition, comp, task_path)
                            futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                        print(f"Completed: {result.composition.composition_id} on {result.task_id}")
                    except Exception as e:
                        print(f"Error: {e}")
        else:
            for comp in compositions:
                for task_id in task_ids:
                    task_path = self.tasks_dir / task_id
                    if task_path.exists():
                        result = self.evaluate_composition(comp, task_path)
                        all_results.append(result)
                        print(f"Completed: {result.composition.composition_id} on {result.task_id}")
        
        # Analyze results
        analysis = self._analyze_results(all_results)
        
        # Save results
        self._save_results(analysis)
        
        return analysis
    
    def _analyze_results(self, results: List[CompositionResult]) -> CrossModelAnalysis:
        """Analyze cross-model evaluation results"""
        
        if not results:
            raise ValueError("No results to analyze")
        
        # Find best and worst compositions
        sorted_results = sorted(results, key=lambda r: (r.success, r.synergy_score), reverse=True)
        best = sorted_results[0].composition
        worst = sorted_results[-1].composition
        
        # Calculate synergy matrix
        synergy_matrix = {}
        for r in results:
            key = f"{r.composition.planner_model.name}+{r.composition.executor_model.name}"
            if key not in synergy_matrix:
                synergy_matrix[key] = []
            synergy_matrix[key].append(r.synergy_score)
        
        # Average synergies
        for key in synergy_matrix:
            synergy_matrix[key] = np.mean(synergy_matrix[key])
        
        # Calculate model strengths by role
        model_strengths = {}
        
        for model in self.models:
            model_strengths[model.name] = {
                "as_planner": np.mean([r.score for r in results if r.composition.planner_model == model]),
                "as_executor": np.mean([r.score for r in results if r.composition.executor_model == model]),
                "as_verifier": np.mean([r.score for r in results if r.composition.verifier_model == model])
            }
        
        return CrossModelAnalysis(
            best_composition=best,
            worst_composition=worst,
            all_results=results,
            synergy_matrix=synergy_matrix,
            model_strengths=model_strengths
        )
    
    def _save_results(self, analysis: CrossModelAnalysis):
        """Save analysis results to disk"""
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"cross_model_analysis_{timestamp}.json"
        
        # Convert to serializable format
        results_data = {
            "timestamp": timestamp,
            "best_composition": {
                "planner": analysis.best_composition.planner_model.name,
                "executor": analysis.best_composition.executor_model.name,
                "verifier": analysis.best_composition.verifier_model.name
            },
            "worst_composition": {
                "planner": analysis.worst_composition.planner_model.name,
                "executor": analysis.worst_composition.executor_model.name,
                "verifier": analysis.worst_composition.verifier_model.name
            },
            "synergy_matrix": analysis.synergy_matrix,
            "model_strengths": analysis.model_strengths,
            "detailed_results": [
                {
                    "composition_id": r.composition.composition_id,
                    "task_id": r.task_id,
                    "success": r.success,
                    "synergy_score": r.synergy_score,
                    "turns": r.turns_used,
                    "cost": r.cost_dollars
                }
                for r in analysis.all_results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Results saved to {output_file}")
        
        # Also create a summary
        self._print_summary(analysis)
    def _print_summary(self, analysis: CrossModelAnalysis):
        """Print analysis summary"""
        
        print("\n" + "="*60)
        print("CROSS-MODEL TEAM EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\n🏆 BEST TEAM COMPOSITION:")
        print(f"  Planner: {analysis.best_composition.planner_model.name}")
        print(f"  Executor: {analysis.best_composition.executor_model.name}")
        print(f"  Verifier: {analysis.best_composition.verifier_model.name}")
        
        print(f"\n💀 WORST TEAM COMPOSITION:")
        print(f"  Planner: {analysis.worst_composition.planner_model.name}")
        print(f"  Executor: {analysis.worst_composition.executor_model.name}")
        print(f"  Verifier: {analysis.worst_composition.verifier_model.name}")
        
        print(f"\n📊 MODEL STRENGTHS BY ROLE:")
        for model, strengths in analysis.model_strengths.items():
            print(f"  {model}:")
            print(f"    As Planner: {strengths['as_planner']:.2%}")
            print(f"    As Executor: {strengths['as_executor']:.2%}")
            print(f"    As Verifier: {strengths['as_verifier']:.2%}")
        
        print(f"\n🤝 TOP SYNERGISTIC PAIRS:")
        sorted_synergy = sorted(analysis.synergy_matrix.items(), key=lambda x: x[1], reverse=True)[:5]
        for pair, score in sorted_synergy:
            print(f"  {pair}: {score:.3f}")
        
        print("\n" + "="*60)
