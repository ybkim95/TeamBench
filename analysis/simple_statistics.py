#!/usr/bin/env python3
"""
Simple statistical analysis for TeamBench pilot results.
Basic hypothesis testing without external dependencies.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class SimpleTestResult:
    """Simple test result"""
    hypothesis: str
    test_statistic: float
    p_value: float
    effect_size: float
    interpretation: str
    significant: bool

class SimpleAnalyzer:
    """Basic statistical analysis without external dependencies"""
    
    def __init__(self, data_path: str = "experiments/controlled_results"):
        self.data_path = Path(data_path)
    
    def load_data(self) -> List[Dict]:
        """Load all experiment results"""
        results = []
        for file in self.data_path.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                results.append(data)
        return results
    
    def test_scaling_hypothesis(self, data: List[Dict]) -> SimpleTestResult:
        """Test if team benefit correlates with model capability"""
        
        # Calculate team benefit per model
        model_benefits = {}
        
        for result in data:
            model = result['model']
            condition = result['condition']
            score = result['score']
            capability = result['capability']
            
            if model not in model_benefits:
                model_benefits[model] = {
                    'capability': capability,
                    'oracle_scores': [],
                    'team_scores': []
                }
            
            if condition == 'oracle-1x':
                model_benefits[model]['oracle_scores'].append(score)
            elif condition == 'team-standard':
                model_benefits[model]['team_scores'].append(score)
        
        # Calculate correlations
        capabilities = []
        benefits = []
        
        for model, data in model_benefits.items():
            if data['oracle_scores'] and data['team_scores']:
                oracle_avg = sum(data['oracle_scores']) / len(data['oracle_scores'])
                team_avg = sum(data['team_scores']) / len(data['team_scores'])
                benefit = team_avg - oracle_avg
                
                capabilities.append(data['capability'])
                benefits.append(benefit)
        
        if len(capabilities) < 3:
            return SimpleTestResult(
                hypothesis="H1_scaling",
                test_statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                interpretation="Insufficient data for correlation test",
                significant=False
            )
        
        # Simple correlation calculation
        correlation = self._pearson_correlation(capabilities, benefits)
        
        # Simple t-test for correlation significance
        t_stat = correlation * math.sqrt((len(capabilities) - 2) / (1 - correlation**2))
        p_value = self._t_test_p_value(abs(t_stat), len(capabilities) - 2)
        
        interpretation = f"Correlation r={correlation:.3f}"
        if correlation < -0.5:
            interpretation += " suggests strong inverse scaling (weaker models benefit more)"
        elif correlation < -0.3:
            interpretation += " suggests moderate inverse scaling"
        else:
            interpretation += " shows weak or no scaling effect"
        
        return SimpleTestResult(
            hypothesis="H1_scaling",
            test_statistic=correlation,
            p_value=p_value,
            effect_size=abs(correlation),
            interpretation=interpretation,
            significant=p_value < 0.05
        )
    
    def test_compute_control(self, data: List[Dict]) -> SimpleTestResult:
        """Test if team benefit exceeds compute-matched oracle"""
        
        team_scores = []
        oracle_3x_scores = []
        
        # Group by model and task
        paired_data = {}
        
        for result in data:
            key = (result['model'], result['task_id'])
            if key not in paired_data:
                paired_data[key] = {}
            
            paired_data[key][result['condition']] = result['score']
        
        # Extract paired observations
        for key, scores in paired_data.items():
            if 'team-standard' in scores and 'oracle-3x' in scores:
                team_scores.append(scores['team-standard'])
                oracle_3x_scores.append(scores['oracle-3x'])
        
        if len(team_scores) < 5:
            return SimpleTestResult(
                hypothesis="H2_compute_control",
                test_statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                interpretation="Insufficient paired data for compute control test",
                significant=False
            )
        
        # Paired t-test
        differences = [team - oracle for team, oracle in zip(team_scores, oracle_3x_scores)]
        mean_diff = sum(differences) / len(differences)
        
        if len(differences) == 1:
            return SimpleTestResult(
                hypothesis="H2_compute_control", 
                test_statistic=mean_diff,
                p_value=0.5,
                effect_size=abs(mean_diff),
                interpretation=f"Single observation: team-oracle difference = {mean_diff:.3f}",
                significant=False
            )
        
        # Calculate standard error
        var_diff = sum((d - mean_diff)**2 for d in differences) / (len(differences) - 1)
        se_diff = math.sqrt(var_diff / len(differences))
        
        t_stat = mean_diff / se_diff if se_diff > 0 else 0
        p_value = self._t_test_p_value(abs(t_stat), len(differences) - 1)
        
        interpretation = f"Team vs Oracle-3x difference: {mean_diff:.3f}"
        if mean_diff > 0.05:
            interpretation += " (team advantage after compute control)"
        elif mean_diff < -0.05:
            interpretation += " (compute explains team benefit)"
        else:
            interpretation += " (no clear advantage)"
        
        return SimpleTestResult(
            hypothesis="H2_compute_control",
            test_statistic=t_stat,
            p_value=p_value,
            effect_size=abs(mean_diff),
            interpretation=interpretation,
            significant=p_value < 0.05 and mean_diff > 0
        )
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = len(x)
        if n == 0:
            return 0.0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _t_test_p_value(self, t_stat: float, df: int) -> float:
        """Approximate p-value for t-test (two-tailed)"""
        # Very rough approximation for demonstration
        if df <= 1:
            return 1.0
        
        # For df >= 30, t-distribution ≈ normal
        if df >= 30:
            # Rough normal approximation
            if t_stat > 2.576:
                return 0.01  # p < 0.01
            elif t_stat > 1.96:
                return 0.05  # p ≈ 0.05
            elif t_stat > 1.645:
                return 0.1   # p ≈ 0.1
            else:
                return 0.5   # p > 0.1
        
        # For small df, be more conservative
        if t_stat > 3.0:
            return 0.01
        elif t_stat > 2.0:
            return 0.05
        elif t_stat > 1.5:
            return 0.1
        else:
            return 0.5
    
    def generate_report(self, results: List[SimpleTestResult]) -> str:
        """Generate text report"""
        
        report = []
        report.append("=" * 60)
        report.append("TEAMBENCH PILOT ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        for result in results:
            report.append(f"Hypothesis: {result.hypothesis}")
            report.append(f"  Test statistic: {result.test_statistic:.4f}")
            report.append(f"  P-value: {result.p_value:.4f}")
            report.append(f"  Effect size: {result.effect_size:.3f}")
            report.append(f"  Significant: {'YES' if result.significant else 'NO'}")
            report.append(f"  Interpretation: {result.interpretation}")
            report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self) -> Dict:
        """Run complete analysis"""
        
        data = self.load_data()
        if not data:
            print("No data found!")
            return {}
        
        print(f"Loaded {len(data)} experiments")
        
        # Run tests
        results = []
        
        print("Testing scaling hypothesis...")
        results.append(self.test_scaling_hypothesis(data))
        
        print("Testing compute control hypothesis...")
        results.append(self.test_compute_control(data))
        
        # Generate report
        report = self.generate_report(results)
        print("\n" + report)
        
        # Save report
        output_dir = Path("analysis")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "pilot_statistical_report.txt", "w") as f:
            f.write(report)
        
        analysis_data = {
            "results": [
                {
                    "hypothesis": r.hypothesis,
                    "test_statistic": r.test_statistic,
                    "p_value": r.p_value,
                    "effect_size": r.effect_size,
                    "interpretation": r.interpretation,
                    "significant": r.significant
                }
                for r in results
            ],
            "summary": {
                "total_experiments": len(data),
                "significant_findings": sum(1 for r in results if r.significant),
                "total_hypotheses": len(results)
            }
        }
        
        with open(output_dir / "pilot_analysis.json", "w") as f:
            json.dump(analysis_data, f, indent=2)
        
        return analysis_data

def main():
    """Run pilot analysis"""
    
    analyzer = SimpleAnalyzer()
    results = analyzer.run_analysis()
    
    if results:
        summary = results["summary"]
        print(f"\n=== SUMMARY ===")
        print(f"Total experiments: {summary['total_experiments']}")
        print(f"Significant findings: {summary['significant_findings']}/{summary['total_hypotheses']}")
        
        if summary['significant_findings'] > 0:
            print("✓ Some hypotheses supported - methodology validation successful")
        else:
            print("⚠ No significant findings - may need more data or better controls")

if __name__ == "__main__":
    main()