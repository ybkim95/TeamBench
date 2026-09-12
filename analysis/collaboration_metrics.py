"""
Rigorous multi-agent collaboration metrics for TeamBench.

Computes:
1. McNemar's Test (task-level concordance/discordance)
2. Partial Score Improvement (Wilcoxon signed-rank)
3. Effect Size (Cohen's h, Odds Ratio with CI)
4. Assembly Bonus Effect (synergy beyond best 2-role team)
5. Cross-Model Collaboration Consistency (Kendall's W)
6. Difficulty-Stratified Collaboration Benefit
7. Error Recovery Rate (remediation effectiveness)
"""

import json
import os
import glob
import math
import numpy as np
from collections import defaultdict
from scipy import stats as scipy_stats
from typing import Dict, List, Tuple, Optional

# ── Data Loading ──────────────────────────────────────────────────────────

def load_all_results(results_dir: str) -> Dict[str, List[dict]]:
    """Load all result files, group runs by model."""
    model_runs = defaultdict(list)
    
    for f in sorted(glob.glob(f"{results_dir}/*.json")):
        try:
            d = json.load(open(f))
            runs = d.get("runs", [])
            if not runs:
                continue
            
            model = d.get("model", "")
            if not model:
                continue
            
            # Normalize model names
            model_name = normalize_model_name(model)
            if not model_name:
                continue
            
            for r in runs:
                r["_source_file"] = os.path.basename(f)
                r["_model_name"] = model_name
                # Normalize pass field
                if "passed" in r and "pass" not in r:
                    r["pass"] = r["passed"]
                if "partial_score" not in r and "partial" in r:
                    r["partial_score"] = r["partial"]
                model_runs[model_name].append(r)
        except Exception:
            continue
    
    return dict(model_runs)


def normalize_model_name(model: str) -> Optional[str]:
    """Normalize model names to short form."""
    m = model.lower()
    if "sonnet-4-6" in m or "sonnet46" in m:
        return "claude-sonnet-4.6"
    if "haiku-4-5" in m or "haiku45" in m:
        return "claude-haiku-4.5"
    if "gemini-3-flash" in m and "lite" not in m and "3.1" not in m:
        return "gemini-3-flash"
    if "gemini-3.1-flash-lite" in m or "g31lite" in m:
        return "gemini-3.1-lite"
    if "gemini-3.1-pro" in m:
        return "gemini-3.1-pro"
    if "gpt-5.4" in m and "nano" not in m and "mini" not in m:
        return "gpt-5.4"
    if "gpt-5-mini" in m or "gpt5mini" in m:
        return "gpt-5-mini"
    if "gpt-5-nano" in m or "gpt5nano" in m:
        return "gpt-5-nano"
    if "gpt-5.3" in m:
        return "gpt-5.3-chat"
    if "gpt-oss-20b" in m:
        return "gpt-oss-20b"
    if "qwen3.5-0.8b" in m:
        return "qwen3.5-0.8b"
    if "qwen3.5-2b" in m:
        return "qwen3.5-2b"
    if "qwen3.5-4b" in m:
        return "qwen3.5-4b"
    if "qwen3.5-9b" in m:
        return "qwen3.5-9b"
    if "qwen3.5-27b" in m:
        return "qwen3.5-27b"
    if "qwen3.5-35b" in m:
        return "qwen3.5-35b-a3b"
    if "qwen3-14b" in m:
        return "qwen3-14b"
    if "qwen3-8b" in m:
        return "qwen3-8b"
    if "qwen3-4b" in m:
        return "qwen3-4b"
    if "qwen3-coder" in m:
        return "qwen3-coder-30b"
    if "qwen2.5-coder" in m:
        return "qwen2.5-coder-32b"
    if "codegemma" in m:
        return "codegemma-7b"
    if "deepseek-r1" in m:
        return "deepseek-r1-32b"
    if "devstral" in m:
        return "devstral-24b"
    if "gemma-3-27b" in m:
        return "gemma3-27b"
    if "glm-4-9b" in m:
        return "glm4-9b"
    if "phi-4-mini" in m:
        return "phi4-mini"
    if "phi-4" in m:
        return "phi4-14b"
    return None


def get_task_results(runs: List[dict], condition: str) -> Dict[str, dict]:
    """Get per-task results for a condition. Deduplicates by keeping best."""
    task_results = {}
    for r in runs:
        if r.get("condition") != condition:
            continue
        tid = r.get("task_id") or r.get("task")
        if not tid:
            continue
        if tid not in task_results:
            task_results[tid] = r
        else:
            old = task_results[tid]
            old_score = (1 if old.get("pass") else 0, old.get("partial_score", 0) or 0)
            new_score = (1 if r.get("pass") else 0, r.get("partial_score", 0) or 0)
            if new_score > old_score:
                task_results[tid] = r
    return task_results


# ── Metric 1: McNemar's Test ─────────────────────────────────────────────

def mcnemar_test(oracle_results: dict, full_results: dict) -> dict:
    """
    McNemar's test for paired nominal data.
    Tests whether discordant pairs are symmetric.
    
    Returns concordance table + test statistic + p-value.
    """
    common_tasks = set(oracle_results.keys()) & set(full_results.keys())
    if len(common_tasks) < 5:
        return {"n_tasks": len(common_tasks), "error": "too few paired tasks"}
    
    # 2x2 concordance table
    both_pass = 0      # oracle=PASS, full=PASS
    oracle_only = 0    # oracle=PASS, full=FAIL
    full_only = 0      # oracle=FAIL, full=PASS (team-unique wins)
    both_fail = 0      # oracle=FAIL, full=FAIL
    
    for tid in common_tasks:
        o_pass = bool(oracle_results[tid].get("pass"))
        f_pass = bool(full_results[tid].get("pass"))
        if o_pass and f_pass:
            both_pass += 1
        elif o_pass and not f_pass:
            oracle_only += 1
        elif not o_pass and f_pass:
            full_only += 1
        else:
            both_fail += 1
    
    # McNemar's test (with continuity correction)
    b = oracle_only  # discordant: oracle wins
    c = full_only    # discordant: team wins
    
    if b + c == 0:
        chi2, p_value = 0.0, 1.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        p_value = 1 - scipy_stats.chi2.cdf(chi2, df=1)
    
    return {
        "n_tasks": len(common_tasks),
        "both_pass": both_pass,
        "oracle_only": oracle_only,
        "team_only": full_only,
        "both_fail": both_fail,
        "team_unique_win_rate": full_only / len(common_tasks),
        "oracle_unique_win_rate": oracle_only / len(common_tasks),
        "mcnemar_chi2": round(chi2, 4),
        "mcnemar_p": round(p_value, 6),
        "significant_005": p_value < 0.05,
    }


# ── Metric 2: Partial Score Improvement (Wilcoxon) ───────────────────────

def partial_score_analysis(oracle_results: dict, full_results: dict) -> dict:
    """
    Paired Wilcoxon signed-rank test on partial scores.
    Tests whether team systematically improves partial scores.
    """
    common_tasks = set(oracle_results.keys()) & set(full_results.keys())
    
    oracle_partials = []
    full_partials = []
    diffs = []
    
    for tid in sorted(common_tasks):
        o_p = oracle_results[tid].get("partial_score", 0) or 0
        f_p = full_results[tid].get("partial_score", 0) or 0
        oracle_partials.append(o_p)
        full_partials.append(f_p)
        diffs.append(f_p - o_p)
    
    if len(diffs) < 5:
        return {"error": "too few paired tasks"}
    
    diffs = np.array(diffs)
    oracle_partials = np.array(oracle_partials)
    full_partials = np.array(full_partials)
    
    # Wilcoxon signed-rank test (two-sided)
    # Filter out zero differences
    nonzero = diffs[diffs != 0]
    if len(nonzero) < 5:
        w_stat, w_p = float('nan'), float('nan')
    else:
        w_stat, w_p = scipy_stats.wilcoxon(nonzero, alternative='two-sided')
    
    # One-sided: team > oracle
    if len(nonzero) >= 5:
        _, w_p_greater = scipy_stats.wilcoxon(nonzero, alternative='greater')
    else:
        w_p_greater = float('nan')
    
    improved = int(np.sum(diffs > 0))
    worsened = int(np.sum(diffs < 0))
    tied = int(np.sum(diffs == 0))
    
    return {
        "n_tasks": len(diffs),
        "mean_oracle_partial": round(float(np.mean(oracle_partials)), 4),
        "mean_full_partial": round(float(np.mean(full_partials)), 4),
        "mean_improvement": round(float(np.mean(diffs)), 4),
        "median_improvement": round(float(np.median(diffs)), 4),
        "improved": improved,
        "worsened": worsened,
        "tied": tied,
        "wilcoxon_stat": round(float(w_stat), 2) if not np.isnan(w_stat) else None,
        "wilcoxon_p_twosided": round(float(w_p), 6) if not np.isnan(w_p) else None,
        "wilcoxon_p_greater": round(float(w_p_greater), 6) if not np.isnan(w_p_greater) else None,
        "significant_005": bool(w_p < 0.05) if not np.isnan(w_p) else None,
    }


# ── Metric 3: Effect Size ────────────────────────────────────────────────

def effect_size_analysis(oracle_results: dict, full_results: dict) -> dict:
    """
    Cohen's h for comparing two proportions.
    Odds Ratio with 95% CI.
    Number Needed to Treat (NNT).
    """
    common_tasks = set(oracle_results.keys()) & set(full_results.keys())
    n = len(common_tasks)
    if n < 5:
        return {"error": "too few tasks"}
    
    o_pass = sum(1 for t in common_tasks if oracle_results[t].get("pass"))
    f_pass = sum(1 for t in common_tasks if full_results[t].get("pass"))
    
    p_oracle = o_pass / n
    p_full = f_pass / n
    
    # Cohen's h
    h1 = 2 * math.asin(math.sqrt(p_full))
    h2 = 2 * math.asin(math.sqrt(p_oracle))
    cohens_h = h1 - h2
    
    # Effect size interpretation
    if abs(cohens_h) < 0.2:
        h_interp = "negligible"
    elif abs(cohens_h) < 0.5:
        h_interp = "small"
    elif abs(cohens_h) < 0.8:
        h_interp = "medium"
    else:
        h_interp = "large"
    
    # Odds Ratio (with Haldane correction for zero cells)
    a = f_pass + 0.5
    b = (n - f_pass) + 0.5
    c = o_pass + 0.5
    d = (n - o_pass) + 0.5
    odds_ratio = (a * d) / (b * c)
    log_or = math.log(odds_ratio)
    se_log_or = math.sqrt(1/a + 1/b + 1/c + 1/d)
    or_ci_lower = math.exp(log_or - 1.96 * se_log_or)
    or_ci_upper = math.exp(log_or + 1.96 * se_log_or)
    
    # NNT (Number Needed to Treat)
    ard = p_full - p_oracle  # Absolute Risk Difference
    nnt = 1 / ard if ard > 0 else float('inf')
    
    # Two-proportion z-test
    p_pooled = (o_pass + f_pass) / (2 * n)
    if p_pooled > 0 and p_pooled < 1:
        se = math.sqrt(2 * p_pooled * (1 - p_pooled) / n)
        z = (p_full - p_oracle) / se
        z_p = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
    else:
        z, z_p = 0.0, 1.0
    
    return {
        "n_tasks": n,
        "oracle_pass_rate": round(p_oracle, 4),
        "full_pass_rate": round(p_full, 4),
        "absolute_uplift": round(p_full - p_oracle, 4),
        "relative_uplift": round((p_full - p_oracle) / max(p_oracle, 0.001), 4),
        "cohens_h": round(cohens_h, 4),
        "cohens_h_interpretation": h_interp,
        "odds_ratio": round(odds_ratio, 4),
        "odds_ratio_ci95": [round(or_ci_lower, 4), round(or_ci_upper, 4)],
        "nnt": round(nnt, 2) if nnt != float('inf') else None,
        "z_test_p": round(z_p, 6),
        "significant_005": z_p < 0.05,
    }


# ── Metric 4: Assembly Bonus Effect ──────────────────────────────────────

def assembly_bonus(runs: List[dict]) -> Optional[dict]:
    """
    Assembly Bonus = P(full) - max(P(team_no_plan), P(team_no_verify))
    Tests whether synergy of all roles exceeds best two-role config.
    """
    full = get_task_results(runs, "full")
    tnp = get_task_results(runs, "team_no_plan")
    tnv = get_task_results(runs, "team_no_verify")
    
    if not full or not tnp or not tnv:
        return None
    
    common = set(full.keys()) & set(tnp.keys()) & set(tnv.keys())
    if len(common) < 5:
        return None
    
    n = len(common)
    full_pass = sum(1 for t in common if full[t].get("pass"))
    tnp_pass = sum(1 for t in common if tnp[t].get("pass"))
    tnv_pass = sum(1 for t in common if tnv[t].get("pass"))
    
    p_full = full_pass / n
    p_tnp = tnp_pass / n
    p_tnv = tnv_pass / n
    p_best_ablated = max(p_tnp, p_tnv)
    
    abe = p_full - p_best_ablated
    
    return {
        "n_tasks": n,
        "full_rate": round(p_full, 4),
        "team_no_plan_rate": round(p_tnp, 4),
        "team_no_verify_rate": round(p_tnv, 4),
        "best_ablated_rate": round(p_best_ablated, 4),
        "best_ablated": "team_no_plan" if p_tnp >= p_tnv else "team_no_verify",
        "assembly_bonus": round(abe, 4),
        "synergy_exists": abe > 0,
        "planning_value": round(p_full - p_tnp, 4),
        "verification_value": round(p_full - p_tnv, 4),
    }


# ── Metric 5: Cross-Model Collaboration Consistency (Kendall's W) ────────

def kendall_w_collaboration(model_runs: Dict[str, List[dict]]) -> dict:
    """
    Kendall's W (coefficient of concordance) across models.
    Tests whether different models agree on which tasks benefit from teamwork.
    
    Each model is a "rater", each task is an "item", the rating is 
    the collaboration benefit (full_partial - oracle_partial).
    """
    # Get models with both oracle and full
    model_benefits = {}
    all_tasks = set()
    
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        if len(common) < 10:
            continue
        
        benefits = {}
        for tid in common:
            o_p = oracle[tid].get("partial_score", 0) or 0
            f_p = full[tid].get("partial_score", 0) or 0
            benefits[tid] = f_p - o_p
        
        model_benefits[model] = benefits
        all_tasks |= common
    
    if len(model_benefits) < 3:
        return {"error": "need >=3 models with oracle+full data"}
    
    # Find tasks present in ALL qualifying models
    common_tasks = set.intersection(*[set(b.keys()) for b in model_benefits.values()])
    if len(common_tasks) < 5:
        return {"error": f"only {len(common_tasks)} common tasks across models"}
    
    common_tasks = sorted(common_tasks)
    models = sorted(model_benefits.keys())
    k = len(models)  # number of raters
    n = len(common_tasks)  # number of items
    
    # Build rank matrix
    rank_matrix = np.zeros((k, n))
    for i, model in enumerate(models):
        values = [model_benefits[model][t] for t in common_tasks]
        rank_matrix[i] = scipy_stats.rankdata(values)
    
    # Kendall's W
    rank_sums = rank_matrix.sum(axis=0)
    mean_rank_sum = np.mean(rank_sums)
    S = np.sum((rank_sums - mean_rank_sum) ** 2)
    W = 12 * S / (k ** 2 * (n ** 3 - n))
    
    # Chi-square approximation for significance
    chi2 = k * (n - 1) * W
    df = n - 1
    p_value = 1 - scipy_stats.chi2.cdf(chi2, df)
    
    # Interpretation
    if W < 0.1:
        interp = "no agreement"
    elif W < 0.3:
        interp = "weak agreement"
    elif W < 0.5:
        interp = "moderate agreement"
    elif W < 0.7:
        interp = "strong agreement"
    else:
        interp = "very strong agreement"
    
    # Find most consistently team-helped tasks
    mean_benefits = {t: np.mean([model_benefits[m][t] for m in models]) 
                     for t in common_tasks}
    std_benefits = {t: np.std([model_benefits[m][t] for m in models])
                    for t in common_tasks}
    
    # Tasks where ALL models agree on direction
    consistently_helped = []
    consistently_hurt = []
    for t in common_tasks:
        vals = [model_benefits[m][t] for m in models]
        if all(v > 0 for v in vals):
            consistently_helped.append((t, mean_benefits[t]))
        elif all(v < 0 for v in vals):
            consistently_hurt.append((t, mean_benefits[t]))
    
    consistently_helped.sort(key=lambda x: -x[1])
    consistently_hurt.sort(key=lambda x: x[1])
    
    return {
        "n_models": k,
        "models": models,
        "n_common_tasks": n,
        "kendalls_W": round(float(W), 4),
        "interpretation": interp,
        "chi2": round(float(chi2), 4),
        "p_value": round(float(p_value), 6),
        "significant_005": p_value < 0.05,
        "consistently_team_helped": consistently_helped[:10],
        "consistently_team_hurt": consistently_hurt[:10],
        "n_consistently_helped": len(consistently_helped),
        "n_consistently_hurt": len(consistently_hurt),
    }


# ── Metric 6: Difficulty-Stratified Analysis ─────────────────────────────

def difficulty_stratified(model_runs: Dict[str, List[dict]]) -> dict:
    """
    Bin tasks by oracle difficulty (pooled across models),
    measure teamwork benefit per difficulty bin.
    """
    # Pool oracle results across all models
    task_oracle_rates = defaultdict(list)
    task_full_rates = defaultdict(list)
    
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        if len(oracle) < 10:
            continue
        for tid, r in oracle.items():
            task_oracle_rates[tid].append(1 if r.get("pass") else 0)
        for tid, r in full.items():
            task_full_rates[tid].append(1 if r.get("pass") else 0)
    
    # Compute pooled oracle pass rate per task
    task_difficulty = {}
    for tid, rates in task_oracle_rates.items():
        task_difficulty[tid] = np.mean(rates)
    
    # Bin: easy (oracle > 0.5), medium (0.1 < oracle <= 0.5), hard (oracle <= 0.1)
    bins = {
        "hard (oracle ≤ 10%)": [],
        "medium (10% < oracle ≤ 50%)": [],
        "easy (oracle > 50%)": [],
    }
    
    for tid, orc_rate in task_difficulty.items():
        if tid not in task_full_rates:
            continue
        full_rate = np.mean(task_full_rates[tid])
        benefit = full_rate - orc_rate
        
        if orc_rate <= 0.1:
            bins["hard (oracle ≤ 10%)"].append(benefit)
        elif orc_rate <= 0.5:
            bins["medium (10% < oracle ≤ 50%)"].append(benefit)
        else:
            bins["easy (oracle > 50%)"].append(benefit)
    
    result = {}
    for bin_name, benefits in bins.items():
        if len(benefits) >= 3:
            benefits = np.array(benefits)
            # One-sample t-test: is mean benefit > 0?
            t_stat, t_p = scipy_stats.ttest_1samp(benefits, 0)
            result[bin_name] = {
                "n_tasks": len(benefits),
                "mean_benefit": round(float(np.mean(benefits)), 4),
                "std_benefit": round(float(np.std(benefits)), 4),
                "median_benefit": round(float(np.median(benefits)), 4),
                "pct_helped": round(float(np.mean(benefits > 0)), 4),
                "t_stat": round(float(t_stat), 4),
                "t_p": round(float(t_p), 6),
                "significant_005": t_p < 0.05 and np.mean(benefits) > 0,
            }
        else:
            result[bin_name] = {"n_tasks": len(benefits), "error": "too few tasks"}
    
    return result


# ── Metric 7: Role Contribution Analysis ─────────────────────────────────

def role_contribution(runs: List[dict]) -> Optional[dict]:
    """
    Measures unique contribution of each role using Shapley-like decomposition.
    
    Marginal contributions:
    - Planner: P(full) - P(team_no_plan)
    - Verifier: P(full) - P(team_no_verify)
    - Both: P(full) - P(oracle) [gap from restricted to full]
    - Interaction: full - (tnp + tnv - restricted) [superadditive?)
    """
    oracle = get_task_results(runs, "oracle")
    restricted = get_task_results(runs, "restricted")
    full = get_task_results(runs, "full")
    tnp = get_task_results(runs, "team_no_plan")
    tnv = get_task_results(runs, "team_no_verify")
    
    if not all([oracle, restricted, full, tnp, tnv]):
        return None
    
    common = set(oracle.keys()) & set(restricted.keys()) & set(full.keys()) & \
             set(tnp.keys()) & set(tnv.keys())
    if len(common) < 5:
        return None
    
    n = len(common)
    p = lambda results: sum(1 for t in common if results[t].get("pass")) / n
    
    p_oracle = p(oracle)
    p_restricted = p(restricted)
    p_full = p(full)
    p_tnp = p(tnp)
    p_tnv = p(tnv)
    
    # Marginal contributions
    mc_planner = p_full - p_tnp
    mc_verifier = p_full - p_tnv
    
    # Interaction term (superadditivity)
    # If roles are independent: P(full) ≈ P(tnp) + P(tnv) - P(restricted)
    # Interaction = P(full) - [P(tnp) + P(tnv) - P(restricted)]
    interaction = p_full - (p_tnp + p_tnv - p_restricted)
    
    # Shapley values (2-player coalition game)
    # V({}) = P(restricted), V({P}) = P(tnv), V({V}) = P(tnp), V({P,V}) = P(full)
    # Shapley(Planner) = 0.5 * [V({P}) - V({})] + 0.5 * [V({P,V}) - V({V})]
    shapley_planner = 0.5 * (p_tnv - p_restricted) + 0.5 * (p_full - p_tnp)
    shapley_verifier = 0.5 * (p_tnp - p_restricted) + 0.5 * (p_full - p_tnv)
    
    return {
        "n_tasks": n,
        "pass_rates": {
            "restricted": round(p_restricted, 4),
            "team_no_plan": round(p_tnp, 4),
            "team_no_verify": round(p_tnv, 4),
            "full": round(p_full, 4),
            "oracle": round(p_oracle, 4),
        },
        "marginal_contribution": {
            "planner": round(mc_planner, 4),
            "verifier": round(mc_verifier, 4),
        },
        "shapley_values": {
            "planner": round(shapley_planner, 4),
            "verifier": round(shapley_verifier, 4),
        },
        "interaction_term": round(interaction, 4),
        "superadditive": interaction > 0,
    }


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    results_dir = "/u/ybkim95/TeamBench/shared/ablation_results"
    model_runs = load_all_results(results_dir)
    
    print("=" * 80)
    print("TEAMBENCH RIGOROUS COLLABORATION METRICS")
    print("=" * 80)
    
    # Filter to models with meaningful data
    qualifying_models = {}
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        if len(common) >= 10:
            qualifying_models[model] = runs
            print(f"  {model}: {len(common)} paired tasks (oracle+full)")
    
    print(f"\nQualifying models: {len(qualifying_models)}")
    print()
    
    # ── Per-Model Metrics ─────────────────────────────────────────────
    all_results = {}
    
    for model in sorted(qualifying_models.keys()):
        runs = qualifying_models[model]
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        
        print(f"\n{'─' * 70}")
        print(f"MODEL: {model}")
        print(f"{'─' * 70}")
        
        model_result = {}
        
        # 1. McNemar's Test
        mcn = mcnemar_test(oracle, full)
        model_result["mcnemar"] = mcn
        print(f"\n  1. McNemar's Test (n={mcn['n_tasks']})")
        print(f"     Both pass: {mcn.get('both_pass',0)}, Both fail: {mcn.get('both_fail',0)}")
        print(f"     Team-only wins: {mcn.get('team_only',0)} ({mcn.get('team_unique_win_rate',0):.1%})")
        print(f"     Oracle-only wins: {mcn.get('oracle_only',0)} ({mcn.get('oracle_unique_win_rate',0):.1%})")
        sig = "***" if mcn.get('mcnemar_p', 1) < 0.001 else "**" if mcn.get('mcnemar_p', 1) < 0.01 else "*" if mcn.get('mcnemar_p', 1) < 0.05 else "ns"
        print(f"     χ²={mcn.get('mcnemar_chi2',0):.2f}, p={mcn.get('mcnemar_p',1):.4f} {sig}")
        
        # 2. Partial Score Analysis
        psa = partial_score_analysis(oracle, full)
        model_result["partial_score"] = psa
        print(f"\n  2. Partial Score Analysis")
        print(f"     Oracle mean: {psa.get('mean_oracle_partial',0):.3f}, Full mean: {psa.get('mean_full_partial',0):.3f}")
        print(f"     Mean improvement: {psa.get('mean_improvement',0):+.3f}")
        print(f"     Improved/Worsened/Tied: {psa.get('improved',0)}/{psa.get('worsened',0)}/{psa.get('tied',0)}")
        if psa.get('wilcoxon_p_twosided') is not None:
            sig = "***" if psa['wilcoxon_p_twosided'] < 0.001 else "**" if psa['wilcoxon_p_twosided'] < 0.01 else "*" if psa['wilcoxon_p_twosided'] < 0.05 else "ns"
            print(f"     Wilcoxon W={psa.get('wilcoxon_stat')}, p={psa['wilcoxon_p_twosided']:.4f} {sig}")
        
        # 3. Effect Size
        eff = effect_size_analysis(oracle, full)
        model_result["effect_size"] = eff
        print(f"\n  3. Effect Size")
        print(f"     Oracle: {eff.get('oracle_pass_rate',0):.1%}, Full: {eff.get('full_pass_rate',0):.1%}")
        print(f"     Absolute uplift: {eff.get('absolute_uplift',0):+.1%}")
        print(f"     Cohen's h: {eff.get('cohens_h',0):.3f} ({eff.get('cohens_h_interpretation','?')})")
        print(f"     Odds Ratio: {eff.get('odds_ratio',0):.2f} [{eff.get('odds_ratio_ci95',[0,0])[0]:.2f}, {eff.get('odds_ratio_ci95',[0,0])[1]:.2f}]")
        if eff.get('nnt'):
            print(f"     NNT: {eff['nnt']:.1f}")
        
        # 4. Assembly Bonus
        abe = assembly_bonus(runs)
        model_result["assembly_bonus"] = abe
        if abe:
            print(f"\n  4. Assembly Bonus Effect")
            print(f"     Full: {abe['full_rate']:.1%}, Best ablated ({abe['best_ablated']}): {abe['best_ablated_rate']:.1%}")
            print(f"     Assembly bonus: {abe['assembly_bonus']:+.1%}")
            print(f"     Planning value: {abe['planning_value']:+.1%}, Verification value: {abe['verification_value']:+.1%}")
            print(f"     Synergy: {'YES' if abe['synergy_exists'] else 'NO'}")
        
        # 5. Role Contribution
        rc = role_contribution(runs)
        model_result["role_contribution"] = rc
        if rc:
            print(f"\n  5. Role Contribution (Shapley Decomposition)")
            print(f"     Shapley(Planner): {rc['shapley_values']['planner']:+.3f}")
            print(f"     Shapley(Verifier): {rc['shapley_values']['verifier']:+.3f}")
            print(f"     Interaction: {rc['interaction_term']:+.3f} ({'superadditive' if rc['superadditive'] else 'subadditive'})")
        
        all_results[model] = model_result
    
    # ── Cross-Model Metrics ───────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("CROSS-MODEL ANALYSIS")
    print(f"{'=' * 70}")
    
    # 6. Kendall's W
    kw = kendall_w_collaboration(qualifying_models)
    print(f"\n  6. Cross-Model Collaboration Consistency (Kendall's W)")
    if "error" not in kw:
        print(f"     Models: {kw['n_models']}, Common tasks: {kw['n_common_tasks']}")
        print(f"     W = {kw['kendalls_W']:.4f} ({kw['interpretation']})")
        sig = "***" if kw['p_value'] < 0.001 else "**" if kw['p_value'] < 0.01 else "*" if kw['p_value'] < 0.05 else "ns"
        print(f"     χ²={kw['chi2']:.2f}, p={kw['p_value']:.4f} {sig}")
        print(f"     Consistently team-helped: {kw['n_consistently_helped']} tasks")
        print(f"     Consistently team-hurt: {kw['n_consistently_hurt']} tasks")
        if kw['consistently_team_helped']:
            print(f"     Top helped: {', '.join(f'{t[0]}(+{t[1]:.2f})' for t in kw['consistently_team_helped'][:5])}")
        if kw['consistently_team_hurt']:
            print(f"     Top hurt: {', '.join(f'{t[0]}({t[1]:.2f})' for t in kw['consistently_team_hurt'][:5])}")
    else:
        print(f"     {kw['error']}")
    
    # 7. Difficulty-Stratified
    ds = difficulty_stratified(qualifying_models)
    print(f"\n  7. Difficulty-Stratified Collaboration Benefit")
    for bin_name, stats in ds.items():
        if "error" in stats:
            print(f"     {bin_name}: {stats['n_tasks']} tasks ({stats['error']})")
        else:
            sig = "***" if stats['t_p'] < 0.001 else "**" if stats['t_p'] < 0.01 else "*" if stats['t_p'] < 0.05 else "ns"
            print(f"     {bin_name}: n={stats['n_tasks']}, benefit={stats['mean_benefit']:+.3f} ± {stats['std_benefit']:.3f}, "
                  f"{stats['pct_helped']:.0%} helped, t={stats['t_stat']:.2f}, p={stats['t_p']:.4f} {sig}")
    
    # ── Save ──────────────────────────────────────────────────────────
    output = {
        "per_model": all_results,
        "cross_model": {
            "kendalls_w": kw,
            "difficulty_stratified": ds,
        },
        "meta": {
            "n_models": len(qualifying_models),
            "models": sorted(qualifying_models.keys()),
        }
    }
    
    outpath = "/u/ybkim95/TeamBench/shared/paper/collaboration_metrics.json"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    
    # Custom JSON encoder for numpy types
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.bool_):
                return bool(obj)
            return super().default(obj)
    
    with open(outpath, 'w') as f:
        json.dump(output, f, indent=2, cls=NpEncoder)
    print(f"\nResults saved to {outpath}")


if __name__ == "__main__":
    main()
