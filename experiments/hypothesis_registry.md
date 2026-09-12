# TeamBench Hypothesis Registry
*Pre-registration of experimental hypotheses before data collection*

**Registration Date**: 2026-03-30  
**Experiment**: TeamBench Scaling Analysis Pilot  
**Investigators**: TeamBench Research Team  
**Study Design**: Multi-model, multi-task controlled experiment

## Primary Hypotheses

### H1: Inverse Capability-Benefit Scaling
**Formal Statement**: The benefit derived from team coordination is inversely correlated with individual model capability.

**Operational Definition**: 
- Team benefit = avg(team_scores) - avg(oracle_1x_scores) per model
- Model capability = composite score from public benchmarks (HumanEval, MBPP, MMLU)
- Correlation coefficient between capability and team benefit

**Prediction**: 
- Pearson correlation r < -0.3 (moderate inverse relationship)
- Statistical significance p < 0.05 (α = 0.05, two-tailed test)

**Rationale**: Weaker models have more room for improvement through coordination, while stronger models may experience coordination overhead.

### H2: Compute-Controlled Team Advantage  
**Formal Statement**: Team coordination provides benefits beyond what can be explained by increased compute budget alone.

**Operational Definition**:
- Oracle-3x condition: Single agent with 3x token budget (24,000 tokens vs 8,000 baseline)
- Team-standard condition: 3-agent team with standard budget per agent (8,000 tokens each)
- Paired comparison on identical tasks

**Prediction**:
- team_scores > oracle_3x_scores (directional hypothesis)
- Paired t-test p < 0.05, one-tailed test
- Effect size Cohen's d > 0.3 (small to medium effect)

**Rationale**: If teams only help by using more compute, Oracle-3x should match team performance.

## Secondary Hypotheses

### H3: Power Law Scaling Relationship
**Formal Statement**: Team benefit follows a power law relationship with model capability.

**Mathematical Model**: benefit = α × capability^β where β < 0

**Operational Definition**:
- Nonlinear regression: team_benefit ~ α * capability^β
- Bootstrap confidence intervals for α and β parameters  
- Goodness of fit: R² > 0.5

**Prediction**:
- Power law exponent β significantly < 0 (p < 0.05)
- R² > 0.5 indicates good model fit
- Better fit than linear relationship

### H4: Task Difficulty Moderation
**Formal Statement**: Team benefit is greater for more difficult tasks.

**Operational Definition**:
- Task difficulty = 1 - avg(oracle_1x_success_rate) across all models
- Team benefit calculated per task
- Correlation between task difficulty and team benefit

**Prediction**:
- Positive correlation r > 0.2, p < 0.05
- Difficult tasks (success rate < 50%) show larger team benefits

## Experimental Controls

### Control Conditions
1. **Oracle-1x**: Single agent, standard budget (baseline)
2. **Oracle-3x**: Single agent, 3x budget (compute control)  
3. **Team-standard**: 3-agent team, standard budget per agent

### Control Variables
- **Task selection**: Stratified random sampling across difficulty levels
- **Model selection**: Coverage of capability spectrum (65.9 to 75.8 points)
- **Execution order**: Randomized to control for time-of-day effects
- **Token tracking**: Precise measurement for budget controls

## Statistical Analysis Plan

### Multiple Testing Correction
- Benjamini-Hochberg FDR correction for 4 primary/secondary hypotheses
- Family-wise error rate α = 0.05
- Adjusted significance thresholds reported

### Effect Size Reporting
- Pearson correlation coefficients with 95% bootstrap CIs
- Cohen's d for mean differences with 95% CIs  
- R² for model fit with cross-validation

### Power Analysis
- Target power: 80% for medium effect sizes (d = 0.5, r = 0.3)
- Minimum sample size: n ≥ 45 observations per model
- Actual sample size: 45 experiments per model (adequate)

## Deviations and Exceptions

### Planned Deviations
- If < 3 models available: Reduce to correlation analysis only
- If budget exceeded: Stop early and analyze available data
- If infrastructure fails: Switch to manual execution for critical experiments

### Exclusion Criteria
- Experiments with API failures (retry once)
- Tasks with malformed specifications  
- Results with obvious data corruption

## Data Sharing and Transparency

### Open Science Commitments
- Raw experimental data published immediately upon completion
- Analysis code shared in public repository
- Negative results reported with equal prominence
- Failed experiments documented transparently

### Reproducibility Package
- Docker container with exact software environment
- Random seeds logged for all stochastic processes
- Detailed execution logs with timestamps
- Model versions and API endpoints recorded

---

**Registry Signature**: This hypothesis registry is pre-committed before any experimental data collection. Post-hoc modifications to hypotheses or analysis plans will be clearly documented and justified.

**Contact**: Available at TeamBench repository for external validation and replication attempts.