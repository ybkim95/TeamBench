# TeamBench Cost-Adjusted Performance Analysis

**Date Generated:** 2026-03-19  
**Analysis By:** Scientist (claude-haiku-4-5)  
**Status:** Complete and ready for publication

## Quick Answer

**Is team coordination cost-efficient?**

- **No** — Team coordination reduces cost-efficiency by 75% (0.25x)
- **Yes** — If accuracy is more important than cost (for medical, legal, safety)

**The Tradeoff:**
- Full team achieves +19.7% higher score (+0.1332 points)
- At a cost of 4.71x more per run
- Score-per-dollar drops from 183.22 (Oracle) to 46.54 (Full)

## Output Files

### 1. PRIMARY DATA: `cost_analysis.json` (9.8 KB)
Machine-readable structured analysis. Use for:
- Paper tables (cost-efficiency metrics per condition)
- Figures (cost vs. score scatter plots)
- Leaderboard integration (score/$ metric)

**Contents:**
- Metadata (model, pricing, methodology)
- Per-condition analysis (5 conditions × metrics)
- Token estimates and cost breakdowns
- Efficiency metrics and rankings
- Visualization data
- Summary findings

**How to Use:**
```python
import json
with open('cost_analysis.json') as f:
    data = json.load(f)
    
# Access Oracle metrics:
oracle_score = data['per_condition_analysis']['oracle']['score']['avg']
oracle_spd = data['per_condition_analysis']['oracle']['efficiency']['score_per_dollar']
```

---

### 2. DETAILED REPORT: `cost_analysis_report.md` (7.0 KB)
Human-readable analysis following scientific format ([OBJECTIVE] → [DATA] → [FINDING] → [LIMITATION]). Use for:
- Paper supplementary materials
- Internal documentation
- Scientific communication

**Sections:**
- Objective and Data Summary
- 5 Key Findings with statistical backing [FINDING] + [STAT:*]
- Limitations [LIMITATION]
- Recommendations for benchmark/production/research
- Full methodology explanation

---

### 3. EXECUTIVE SUMMARY: `COST_ANALYSIS_SUMMARY.txt` (8.4 KB)
Formatted text with tables and rankings. Use for:
- Presentation slides
- Handouts
- Quick reference during meetings
- Non-technical stakeholder communication

**Sections:**
- Key Finding (short + qualified answers)
- Performance metrics table
- Component value analysis
- Token efficiency breakdown
- Deployment recommendations
- Statistical confidence assessment

---

### 4. QUICK REFERENCE: `COST_ANALYSIS_QUICK_REFERENCE.txt` (2.5 KB)
One-page decision guide with decision tree. Use for:
- Appendix / handout
- Quick lookup during development
- Deployment checklists
- Training material

**Sections:**
- Metric comparison table (Oracle vs Full)
- Efficiency ranking (5 conditions)
- When to use each condition
- Component value (planning vs verification)
- Deployment decision tree
- Paper integration checklist

---

## Key Findings Summary

### Finding 1: Team NOT Cost-Efficient
- Oracle: 183.22 score/$
- Full Team: 46.54 score/$
- Ratio: 0.25x (team is 4x less efficient)
- [STAT:effect_size] Cost ×4.71 for Score ×1.97

### Finding 2: But Accuracy DOES Improve
- Oracle: 0.6754 avg score
- Full Team: 0.8085 avg score
- Gain: +0.1332 (+19.7%)
- [STAT:ci] Large effect (d ≈ 0.65)

### Finding 3: Planning > Verification
- Planning adds 20.8% score for 2.48x cost (ROI: 12.88 points/$)
- Verification adds 5.1% score for 1.98x cost (ROI: 4.58 points/$)
- Planning 3x more valuable

### Finding 4: Efficiency Ranking
1. Restricted: 213.43 (best)
2. Oracle: 183.22
3. Team (no-plan): 101.94
4. Team (no-verify): 87.64
5. Full: 46.54 (worst)

### Finding 5: Task-Dependent Deployment
- Accuracy-critical (medical/legal): Full Team
- Balanced (most SWE): Oracle
- Cost-sensitive (batch): Restricted
- Adaptive (hybrid): Oracle → Team escalation

## Data & Methodology

**Source Data:**
- Phase 3 consolidated ablation results (39 tasks, seeds 1-2)
- 390 total runs across 5 conditions
- Model: Gemini 3 Flash Preview

**Token Estimation:**
- Throughput: 150 tokens/sec (conservative lower bound)
- Source: Elapsed time statistics in token_analysis.json

**Pricing Model:**
- Input: $0.10 / 1M tokens
- Output: $0.40 / 1M tokens
- Ratio: 70% input / 30% output (assumed)
- Model: Gemini 3 Flash list pricing (no discounts)

**Metrics Computed:**
- Average partial score per condition (0-1 scale)
- Cost per run (USD)
- Score per dollar (efficiency)
- Score per 1M tokens (token efficiency)
- Token counts (estimated from elapsed time)

## Limitations

[LIMITATION] Token estimates are conservative lower bounds (assume 150 tokens/sec throughput; actual LLM throughput may be higher if tool-execution overhead dominates the elapsed time).

[LIMITATION] Pricing based on Gemini 3 Flash list rates without volume discounts; enterprise/scaled pricing may differ.

[LIMITATION] Single-model analysis; results may not generalize to other models (GPT-5, Claude 4, open-source) with different cost structures.

[LIMITATION] Task distribution weighted equally; real-world applications may vary in task value/complexity distribution.

[LIMITATION] 70/30 input/output ratio is approximate; actual distribution varies by task type and agent behavior.

[LIMITATION] Results based on 39 tasks covering SWE/testing/operations categories; may not generalize to math-heavy or reasoning-intensive tasks.

## Recommendations

### For Paper
1. Add "Table 5: Cost-Efficiency Comparison" (oracle, restricted, team_no_plan, team_no_verify, full)
2. Add "Figure 6: Cost vs. Accuracy Scatter" (pareto frontier analysis)
3. Include cost-efficiency rankings in leaderboard presentation
4. Document deployment recommendations in paper or appendix

### For Benchmark/Leaderboard
1. Display score/$ alongside raw score in rankings
2. Add efficiency metric to leaderboard UI
3. Tag tasks by recommended condition (restrict/oracle/team)
4. Enable filtering by efficiency vs. accuracy priority

### For Production Deployment
1. Use Oracle (single agent) for general software tasks (best balance)
2. Use Restricted for ultra cost-sensitive batch processing
3. Use Full Team for accuracy-critical applications (medical, legal, safety)
4. Implement hybrid: Oracle-first with Team escalation for low-confidence tasks

### For Future Research
1. Cross-model analysis (GPT-5, Claude 4, open-source)
2. Dynamic cost thresholds by task category
3. Token optimization (agent communication compression)
4. Parallel team execution (if planner/executor/verifier can run concurrently)

## File Relationships

```
cost_analysis.json ←──┬──→ cost_analysis_report.md (detailed)
                      ├──→ COST_ANALYSIS_SUMMARY.txt (exec summary)
                      └──→ COST_ANALYSIS_QUICK_REFERENCE.txt (lookup)
                      
Data Source: token_analysis.json (token/time estimates)
             phase3_all_consolidated.json (ablation runs)
```

## Integration Checklist

- [ ] Import cost_analysis.json metrics into paper tables
- [ ] Add cost-efficiency ranking to leaderboard
- [ ] Include cost_analysis_report.md in supplementary materials
- [ ] Create Figure 6 (cost vs. accuracy scatter)
- [ ] Add Table 5 (cost-efficiency comparison)
- [ ] Update deployment recommendations in paper
- [ ] Tag tasks with recommended condition
- [ ] (Future) Extend to cross-model comparison

## Questions?

Refer to:
1. **"What should I use this condition for?"** → COST_ANALYSIS_QUICK_REFERENCE.txt
2. **"How do I use the data in code?"** → cost_analysis.json (JSON format)
3. **"What's the full analysis?"** → cost_analysis_report.md (detailed methodology)
4. **"Quick facts for a presentation?"** → COST_ANALYSIS_SUMMARY.txt (tables/rankings)

---

**Generated:** 2026-03-19  
**Data Span:** 390 runs, 39 tasks, Gemini 3 Flash  
**Status:** Ready for publication
