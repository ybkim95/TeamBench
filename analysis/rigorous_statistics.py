#!/usr/bin/env python3
"""
Rigorous statistical analysis for TeamBench scaling experiments.
Implements proper hypothesis testing, multiple testing corrections, and scaling law fitting.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
from scipy.optimize import curve_fit
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import TTestPower
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Hypothesis:
    """Pre-registered hypothesis with test specification"""
    name: str
    description: str
    test_type: str  # 't-test', 'correlation', 'regression'
    alpha: float = 0.05
    alternative: str = 'two-sided'
    
@dataclass 
class TestResult:
    """Statistical test result with corrections"""
    hypothesis: str
    statistic: float
    p_value: float
    adjusted_p: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    reject_null: bool
    interpretation: str

class RigorousAnalyzer:
    """Rigorous statistical analysis with pre-registration and corrections"""
    
    def __init__(self, data_path: str = "experiments/controlled_results"):
        self.data_path = Path(data_path)
        
        # Pre-registered hypotheses
        self.hypotheses = [
            Hypothesis(
                "H1_scaling",
                "Team benefit inversely correlates with model capability",
                "correlation",
                alpha=0.01
            ),
            Hypothesis(
                "H2_power_law",
                "Benefit follows power law: benefit = α × capability^β, β < 0",
                "regression",
                alpha=0.05
            ),
            Hypothesis(
                "H3_cross_model",
                "Cross-model teams outperform homogeneous teams",
                "t-test",
                alpha=0.05
            ),
            Hypothesis(
                "H4_compute",
                "Team benefit exceeds compute-matched oracle",
                "t-test",
                alpha=0.05,
                alternative='greater'
            ),
            Hypothesis(
                "H5_threshold",
                "Team benefit > 5% for models with capability < 75",
                "t-test",
                alpha=0.05,
                alternative='greater'
            )
        ]
        
    def load_data(self) -> pd.DataFrame:
        """Load experimental results into DataFrame"""
        
        results = []
        for file in self.data_path.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                results.append(data)
        
        df = pd.DataFrame(results)
        
        # Add capability scores (would be fetched from benchmarks)
        capability_map = {
            "gpt-4": 85,
            "gpt-4o": 87,
            "gpt-4o-mini": 72,
            "claude-3-opus": 94,
            "claude-3-sonnet": 83,
            "claude-3-haiku": 68,
            "gemini-1.5-pro": 86,
            "gemini-1.5-flash": 75,
            # Add more as needed
        }
        
        df['capability'] = df['model'].map(capability_map)
        
        return df
    
    def calculate_power_analysis(self, effect_size: float = 0.5) -> Dict:
        """Calculate required sample size for desired power"""
        
        power_analyzer = TTestPower()
        
        # For each hypothesis
        results = {}
        for hyp in self.hypotheses:
            n_required = power_analyzer.solve_power(
                effect_size=effect_size,
                power=0.8,
                alpha=hyp.alpha,
                alternative=hyp.alternative
            )
            
            results[hyp.name] = {
                "required_n": int(np.ceil(n_required)),
                "effect_size": effect_size,
                "power": 0.8,
                "alpha": hyp.alpha
            }
        
        return results
    
    def test_h1_scaling(self, df: pd.DataFrame) -> TestResult:
        """Test H1: Team benefit inversely correlates with capability"""
        
        # Calculate team benefit per model
        team_benefit = []
        capabilities = []
        
        for model in df['model'].unique():
            model_df = df[df['model'] == model]
            
            oracle_score = model_df[model_df['condition'] == 'oracle-1x']['score'].mean()
            team_score = model_df[model_df['condition'] == 'team-standard']['score'].mean()
            
            if not np.isnan(oracle_score) and not np.isnan(team_score):
                benefit = team_score - oracle_score
                team_benefit.append(benefit)
                capabilities.append(model_df['capability'].iloc[0])
        
        # Pearson correlation
        r, p_value = stats.pearsonr(capabilities, team_benefit)
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = self._bootstrap_correlation_ci(
            capabilities, team_benefit
        )
        
        # Cohen's d for effect size
        effect_size = abs(r)  # For correlation, r itself is the effect size
        
        return TestResult(
            hypothesis="H1_scaling",
            statistic=r,
            p_value=p_value,
            adjusted_p=p_value,  # Will be adjusted later
            effect_size=effect_size,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            reject_null=p_value < 0.01,
            interpretation=f"Correlation r={r:.3f} indicates {'strong' if abs(r) > 0.7 else 'moderate'} inverse relationship"
        )
    
    def test_h2_power_law(self, df: pd.DataFrame) -> TestResult:
        """Test H2: Benefit follows power law"""
        
        # Prepare data
        X, Y = [], []
        for model in df['model'].unique():
            model_df = df[df['model'] == model]
            capability = model_df['capability'].iloc[0]
            
            oracle = model_df[model_df['condition'] == 'oracle-1x']['score'].mean()
            team = model_df[model_df['condition'] == 'team-standard']['score'].mean()
            
            if not np.isnan(oracle) and not np.isnan(team):
                X.append(capability)
                Y.append(team - oracle)
        
        X, Y = np.array(X), np.array(Y)
        
        # Fit power law: y = a * x^b
        def power_law(x, a, b):
            return a * np.power(x, b)
        
        try:
            popt, pcov = curve_fit(power_law, X, Y, maxfev=5000)
            a, b = popt
            
            # Calculate R²
            Y_pred = power_law(X, a, b)
            r2 = r2_score(Y, Y_pred)
            
            # Test if b < 0
            b_se = np.sqrt(np.diag(pcov))[1]
            t_stat = b / b_se
            p_value = stats.t.cdf(t_stat, len(X) - 2)  # One-sided test for b < 0
            
            return TestResult(
                hypothesis="H2_power_law",
                statistic=b,
                p_value=p_value,
                adjusted_p=p_value,
                effect_size=r2,
                ci_lower=b - 1.96 * b_se,
                ci_upper=b + 1.96 * b_se,
                reject_null=p_value < 0.05 and b < 0,
                interpretation=f"Power law exponent β={b:.3f}, R²={r2:.3f}"
            )
        except:
            return TestResult(
                hypothesis="H2_power_law",
                statistic=0,
                p_value=1.0,
                adjusted_p=1.0,
                effect_size=0,
                ci_lower=0,
                ci_upper=0,
                reject_null=False,
                interpretation="Power law fitting failed"
            )
    
    def test_h3_cross_model(self, df: pd.DataFrame) -> TestResult:
        """Test H3: Cross-model teams outperform homogeneous"""
        
        # Get cross-model team results
        cross_model_scores = df[
            (df['condition'] == 'team-cross-model')
        ]['score'].values
        
        # Get homogeneous team results
        homogeneous_scores = df[
            (df['condition'] == 'team-standard')
        ]['score'].values
        
        if len(cross_model_scores) == 0 or len(homogeneous_scores) == 0:
            return TestResult(
                hypothesis="H3_cross_model",
                statistic=0,
                p_value=1.0,
                adjusted_p=1.0,
                effect_size=0,
                ci_lower=0,
                ci_upper=0,
                reject_null=False,
                interpretation="Insufficient data for cross-model comparison"
            )
        
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(
            cross_model_scores,
            homogeneous_scores,
            equal_var=False  # Welch's t-test
        )
        
        # Cohen's d
        effect_size = self._cohens_d(cross_model_scores, homogeneous_scores)
        
        # Confidence interval for difference
        diff = np.mean(cross_model_scores) - np.mean(homogeneous_scores)
        se_diff = np.sqrt(
            np.var(cross_model_scores) / len(cross_model_scores) +
            np.var(homogeneous_scores) / len(homogeneous_scores)
        )
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff
        
        return TestResult(
            hypothesis="H3_cross_model",
            statistic=t_stat,
            p_value=p_value,
            adjusted_p=p_value,
            effect_size=effect_size,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            reject_null=p_value < 0.05,
            interpretation=f"Cross-model advantage: {diff:.3f}, Cohen's d={effect_size:.3f}"
        )
    
    def test_h4_compute_control(self, df: pd.DataFrame) -> TestResult:
        """Test H4: Team benefit exceeds compute-matched oracle"""
        
        team_scores = []
        oracle_3x_scores = []
        
        # Pair observations by task and model
        for model in df['model'].unique():
            for task in df['task_id'].unique():
                team = df[
                    (df['model'] == model) & 
                    (df['task_id'] == task) &
                    (df['condition'] == 'team-standard')
                ]['score'].values
                
                oracle = df[
                    (df['model'] == model) &
                    (df['task_id'] == task) &
                    (df['condition'] == 'oracle-3x')
                ]['score'].values
                
                if len(team) > 0 and len(oracle) > 0:
                    team_scores.append(team[0])
                    oracle_3x_scores.append(oracle[0])
        
        if len(team_scores) == 0:
            return TestResult(
                hypothesis="H4_compute",
                statistic=0,
                p_value=1.0,
                adjusted_p=1.0,
                effect_size=0,
                ci_lower=0,
                ci_upper=0,
                reject_null=False,
                interpretation="No paired data for compute control"
            )
        
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(
            team_scores,
            oracle_3x_scores,
            alternative='greater'
        )
        
        # Effect size
        diff = np.mean(np.array(team_scores) - np.array(oracle_3x_scores))
        effect_size = diff / np.std(np.array(team_scores) - np.array(oracle_3x_scores))
        
        # CI for paired difference
        se = stats.sem(np.array(team_scores) - np.array(oracle_3x_scores))
        ci_lower = diff - 1.96 * se
        ci_upper = diff + 1.96 * se
        
        return TestResult(
            hypothesis="H4_compute",
            statistic=t_stat,
            p_value=p_value,
            adjusted_p=p_value,
            effect_size=effect_size,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            reject_null=p_value < 0.05,
            interpretation=f"Team benefit after compute control: {diff:.3f}"
        )
    
    def apply_multiple_testing_correction(
        self,
        results: List[TestResult]
    ) -> List[TestResult]:
        """Apply FDR correction for multiple testing"""
        
        p_values = [r.p_value for r in results]
        
        # Benjamini-Hochberg FDR
        rejected, adjusted_p, _, _ = multipletests(
            p_values,
            alpha=0.05,
            method='fdr_bh'
        )
        
        # Update results with adjusted p-values
        for i, result in enumerate(results):
            result.adjusted_p = adjusted_p[i]
            result.reject_null = rejected[i]
        
        return results
    
    def _bootstrap_correlation_ci(
        self,
        x: List[float],
        y: List[float],
        n_bootstrap: int = 1000
    ) -> Tuple[float, float]:
        """Bootstrap confidence interval for correlation"""
        
        correlations = []
        n = len(x)
        
        for _ in range(n_bootstrap):
            idx = np.random.choice(n, n, replace=True)
            x_boot = [x[i] for i in idx]
            y_boot = [y[i] for i in idx]
            
            r, _ = stats.pearsonr(x_boot, y_boot)
            correlations.append(r)
        
        ci_lower = np.percentile(correlations, 2.5)
        ci_upper = np.percentile(correlations, 97.5)
        
        return ci_lower, ci_upper
    
    def _cohens_d(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """Calculate Cohen's d effect size"""
        
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        # Cohen's d
        d = (np.mean(group1) - np.mean(group2)) / pooled_std
        
        return d
    
    def generate_report(self, results: List[TestResult]) -> str:
        """Generate formatted statistical report"""
        
        report = []
        report.append("=" * 60)
        report.append("TEAMBENCH STATISTICAL ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Power analysis
        report.append("POWER ANALYSIS")
        report.append("-" * 40)
        power = self.calculate_power_analysis()
        for hyp, stats in power.items():
            report.append(f"{hyp}: n={stats['required_n']} for 80% power")
        report.append("")
        
        # Hypothesis tests
        report.append("HYPOTHESIS TESTING RESULTS")
        report.append("-" * 40)
        
        for result in results:
            report.append(f"\n{result.hypothesis}")
            report.append(f"  Statistic: {result.statistic:.4f}")
            report.append(f"  P-value: {result.p_value:.4f}")
            report.append(f"  Adjusted P: {result.adjusted_p:.4f}")
            report.append(f"  Effect Size: {result.effect_size:.3f}")
            report.append(f"  95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
            report.append(f"  Decision: {'REJECT H0' if result.reject_null else 'FAIL TO REJECT H0'}")
            report.append(f"  Interpretation: {result.interpretation}")
        
        # Summary
        report.append("\n" + "=" * 60)
        report.append("SUMMARY")
        report.append("-" * 40)
        
        significant = [r for r in results if r.reject_null]
        report.append(f"Significant findings: {len(significant)}/{len(results)}")
        
        if significant:
            report.append("\nKey findings:")
            for r in significant:
                report.append(f"  - {r.hypothesis}: {r.interpretation}")
        
        return "\n".join(report)
    
    def run_full_analysis(self) -> Dict:
        """Run complete statistical analysis"""
        
        # Load data
        df = self.load_data()
        
        if len(df) == 0:
            print("No data found!")
            return {}
        
        # Test all hypotheses
        results = []
        
        print("Testing H1: Scaling correlation...")
        results.append(self.test_h1_scaling(df))
        
        print("Testing H2: Power law...")
        results.append(self.test_h2_power_law(df))
        
        print("Testing H3: Cross-model teams...")
        results.append(self.test_h3_cross_model(df))
        
        print("Testing H4: Compute control...")
        results.append(self.test_h4_compute_control(df))
        
        # Apply multiple testing correction
        print("Applying FDR correction...")
        results = self.apply_multiple_testing_correction(results)
        
        # Generate report
        report = self.generate_report(results)
        print("\n" + report)
        
        # Save report
        with open("analysis/statistical_report.txt", "w") as f:
            f.write(report)
        
        return {
            "results": [r.__dict__ for r in results],
            "report": report
        }

def main():
    """Run rigorous statistical analysis"""
    
    analyzer = RigorousAnalyzer()
    results = analyzer.run_full_analysis()
    
    # Save results
    with open("analysis/statistical_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()