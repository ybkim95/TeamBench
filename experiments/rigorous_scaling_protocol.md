# TeamBench Rigorous Scaling Experiment Protocol

## 1. Core Scientific Questions

### Primary Hypotheses (Pre-registered)
- **H1**: Team benefit inversely correlates with model capability (measured by established benchmarks)
- **H2**: The relationship follows a power law: `benefit = α × capability^β` where β < 0
- **H3**: Cross-model teams outperform homogeneous teams when roles match model strengths
- **H4**: Team benefit is driven by coordination, not increased compute budget

### Null Hypotheses
- **H0**: Team benefit is independent of model capability
- **H0-compute**: Team benefit is fully explained by 3x compute budget
- **H0-variance**: Observed patterns are statistical noise from high variance

## 2. Model Selection Strategy

### Tier 1: Frontier Models (Must Test)
```python
frontier_models = {
    "gpt-4-turbo-2024-01": {"provider": "openai", "params": "~1T", "cost": "$0.01/1K"},
    "claude-3-opus": {"provider": "anthropic", "params": "~1T", "cost": "$0.015/1K"},
    "gemini-1.5-pro": {"provider": "google", "params": "~1T", "cost": "$0.007/1K"},
    "gpt-4o": {"provider": "openai", "params": "~500B", "cost": "$0.005/1K"}
}
```

### Tier 2: Mid-Tier Models (Critical for Scaling)
```python
mid_tier_models = {
    "claude-3-sonnet": {"provider": "anthropic", "params": "~200B", "cost": "$0.003/1K"},
    "gpt-4o-mini": {"provider": "openai", "params": "~100B", "cost": "$0.00015/1K"},
    "gemini-1.5-flash": {"provider": "google", "params": "~100B", "cost": "$0.00035/1K"},
    "mixtral-8x7b": {"provider": "mistral", "params": "47B", "cost": "$0.0007/1K"}
}
```

### Tier 3: Accessible Models (Volume Testing)
```python
accessible_models = {
    "claude-3-haiku": {"provider": "anthropic", "params": "~50B", "cost": "$0.00025/1K"},
    "llama-3.1-70b": {"provider": "meta", "params": "70B", "cost": "$0.0005/1K"},
    "qwen-2.5-72b": {"provider": "alibaba", "params": "72B", "cost": "$0.0004/1K"},
    "deepseek-v2.5": {"provider": "deepseek", "params": "236B", "cost": "$0.0003/1K"}
}
```

## 3. Control Conditions (Critical for Rigor)

### Compute-Matched Controls
```python
control_conditions = {
    "Oracle-1x": {
        "description": "Single agent, single attempt",
        "compute_budget": 1.0,
        "baseline": True
    },
    "Oracle-3x": {
        "description": "Single agent, 3x token budget",
        "compute_budget": 3.0,
        "controls_for": "compute increase"
    },
    "Oracle-Retry-3": {
        "description": "Single agent, best of 3 attempts",
        "compute_budget": 3.0,
        "controls_for": "variance reduction"
    },
    "Oracle-CoT": {
        "description": "Single agent with chain-of-thought",
        "compute_budget": 1.5,
        "controls_for": "reasoning depth"
    },
    "Team-Budget-Matched": {
        "description": "Team with 1/3 budget per agent",
        "compute_budget": 1.0,
        "controls_for": "fair comparison"
    }
}
```

## 4. Task Selection (Unbiased)

### Stratified Sampling
```python
task_selection = {
    "random_github": {
        "n": 20,
        "source": "Random 'good first issue' from top-100 Python repos",
        "bias": "None - random selection"
    },
    "difficulty_stratified": {
        "n": 30,
        "distribution": {
            "easy": 10,  # Single file, <50 lines
            "medium": 10,  # 2-3 files, <200 lines
            "hard": 10  # Multi-file, >200 lines
        }
    },
    "team_neutral": {
        "n": 20,
        "criteria": "Tasks with no obvious role decomposition",
        "validation": "Independent raters assess team necessity"
    },
    "existing_validated": {
        "n": 30,
        "source": "Top 30 tasks by cross-model agreement",
        "ensures": "Reproducibility"
    }
}
# Total: 100 tasks for scaling analysis
```

## 5. Capability Measurement (Objective)

### Multi-Benchmark Aggregation
```python
capability_metrics = {
    "humaneval_pass1": {"weight": 0.25, "source": "published"},
    "mbpp_pass1": {"weight": 0.25, "source": "published"},
    "mmlu_accuracy": {"weight": 0.20, "source": "published"},
    "gsm8k_accuracy": {"weight": 0.15, "source": "published"},
    "arena_elo": {"weight": 0.15, "source": "lmsys"}
}

def compute_capability_index(model):
    """Weighted average of normalized benchmark scores"""
    scores = fetch_benchmark_scores(model)
    normalized = normalize_to_0_100(scores)
    capability = sum(normalized[k] * capability_metrics[k]["weight"] 
                    for k in capability_metrics)
    return capability
```

## 6. Statistical Analysis Plan

### Power Analysis
```python
from statsmodels.stats.power import TTestPower

# Required sample size for detecting moderate effect (d=0.5)
power_analysis = TTestPower()
n_required = power_analysis.solve_power(
    effect_size=0.5,  # Moderate effect
    power=0.8,  # 80% power
    alpha=0.05 / 5,  # Bonferroni correction for 5 primary hypotheses
    ratio=1.0,
    alternative='two-sided'
)
# Result: Need ~85 task-model pairs per condition
```

### Multiple Testing Correction
```python
from statsmodels.stats.multitest import multipletests

# Benjamini-Hochberg FDR correction
def analyze_with_correction(results):
    p_values = [r.p_value for r in results]
    rejected, adjusted_p, _, _ = multipletests(
        p_values, 
        alpha=0.05, 
        method='fdr_bh'
    )
    return zip(results, adjusted_p, rejected)
```

### Scaling Law Fitting
```python
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

def scaling_law(x, alpha, beta):
    """Power law: benefit = alpha * capability^beta"""
    return alpha * np.power(x, beta)

def fit_scaling_law(capabilities, benefits):
    # Fit with bootstrapped confidence intervals
    popt, pcov = curve_fit(scaling_law, capabilities, benefits)
    
    # Bootstrap for confidence intervals
    n_bootstrap = 1000
    bootstrap_params = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(len(capabilities), len(capabilities), replace=True)
        boot_cap = capabilities[idx]
        boot_ben = benefits[idx]
        boot_popt, _ = curve_fit(scaling_law, boot_cap, boot_ben)
        bootstrap_params.append(boot_popt)
    
    ci_lower = np.percentile(bootstrap_params, 2.5, axis=0)
    ci_upper = np.percentile(bootstrap_params, 97.5, axis=0)
    
    return {
        "alpha": popt[0],
        "beta": popt[1],
        "alpha_ci": (ci_lower[0], ci_upper[0]),
        "beta_ci": (ci_lower[1], ci_upper[1]),
        "r2": r2_score(benefits, scaling_law(capabilities, *popt))
    }
```

## 7. Execution Timeline

### Phase 1: Infrastructure (Week 1)
- [ ] Implement compute-controlled conditions
- [ ] Set up automated experiment runner
- [ ] Create real-time monitoring dashboard
- [ ] Implement checkpointing for long runs

### Phase 2: Pilot (Week 2)
- [ ] Test 3 models on 10 tasks each
- [ ] Validate measurement consistency
- [ ] Tune hyperparameters
- [ ] Estimate variance for power analysis

### Phase 3: Main Experiment (Weeks 3-4)
- [ ] Run 12 models × 100 tasks × 6 conditions
- [ ] Total: 7,200 evaluations
- [ ] Estimated cost: $3,000 (with optimizations)
- [ ] Parallel execution on 10 GPUs

### Phase 4: Analysis (Week 5)
- [ ] Fit scaling laws with confidence intervals
- [ ] Test all hypotheses with corrections
- [ ] Mechanistic analysis of outliers
- [ ] Sensitivity analysis

### Phase 5: Validation (Week 6)
- [ ] Cross-validation on held-out tasks
- [ ] External replication subset
- [ ] Ablation studies
- [ ] Robustness checks

## 8. Expected Outcomes and Impact

### Minimum Viable Contribution
- First rigorous measurement of team scaling laws
- Compute-controlled evidence for/against coordination value
- Reusable infrastructure for future research

### Likely Contributions
- Capability thresholds for team deployment
- Mechanistic understanding of coordination
- Cross-model team optimization strategies

### Best Case Impact
- Fundamental scaling law for multi-agent systems
- Industry adoption as standard benchmark
- Enables principled agent system design

## 9. Risk Mitigation

### Technical Risks
- **Model API failures**: Cache all responses, implement retry logic
- **Computational cost**: Start with smaller subset, scale if promising
- **Reproducibility**: Version lock all dependencies, seed everything

### Scientific Risks
- **Null results**: Still valuable - proves coordination isn't universal
- **Confounding**: Multiple control conditions isolate effects
- **Generalization**: Test on multiple task types and domains

## 10. Transparent Limitations

We will explicitly acknowledge:
- Task selection may not represent all domains
- Model selection limited by API availability
- Scaling laws may not extrapolate beyond tested range
- Three-role decomposition is one of many possible
- Docker isolation doesn't capture all coordination costs

## 11. Open Science Commitment

- Pre-register hypotheses before experiments
- Release all raw data and analysis code
- Provide containerized reproduction environment
- Share negative results prominently
- Enable community extensions

---

## Budget and Resources

### Computational
- API costs: ~$3,000
- GPU hours: 500 hours (A100)
- Storage: 1TB for logs/checkpoints

### Human
- Experiment design: 40 hours
- Execution monitoring: 80 hours
- Analysis and writing: 60 hours
- Total: ~180 hours (4-5 weeks focused)

---

This protocol ensures we make rigorous, reproducible, impactful contributions to the field while being transparent about limitations.