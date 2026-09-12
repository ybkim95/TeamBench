"""
Extended collaboration metrics:
1. Kendall's W with capable models only
2. LaTeX tables
3. Bootstrap confidence intervals
"""

import json
import os
import math
import numpy as np
from scipy import stats as scipy_stats
from collections import defaultdict

# Import from v1
import sys
sys.path.insert(0, "/u/ybkim95/TeamBench")
from analysis.collaboration_metrics import (
    load_all_results, get_task_results, normalize_model_name
)


def bootstrap_ci(data, stat_func=np.mean, n_boot=10000, ci=0.95, seed=42):
    """Bootstrap confidence interval for any statistic."""
    rng = np.random.RandomState(seed)
    data = np.array(data)
    n = len(data)
    boot_stats = np.array([stat_func(rng.choice(data, size=n, replace=True)) for _ in range(n_boot)])
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_stats, 100 * alpha)), float(np.percentile(boot_stats, 100 * (1 - alpha)))


def bootstrap_pass_rate_diff(oracle_passes, full_passes, n_boot=10000, seed=42):
    """Bootstrap CI for difference in pass rates (paired tasks)."""
    rng = np.random.RandomState(seed)
    n = len(oracle_passes)
    diffs = np.array(full_passes, dtype=float) - np.array(oracle_passes, dtype=float)
    boot_diffs = np.array([np.mean(rng.choice(diffs, size=n, replace=True)) for _ in range(n_boot)])
    return float(np.percentile(boot_diffs, 2.5)), float(np.percentile(boot_diffs, 97.5))


def capable_models_kendall_w(model_runs, min_oracle_rate=0.03):
    """Kendall's W restricted to capable models (oracle pass rate > threshold)."""
    qualifying = {}
    
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        if len(common) < 15:
            continue
        
        o_pass = sum(1 for t in common if oracle[t].get("pass"))
        rate = o_pass / len(common)
        if rate >= min_oracle_rate:
            qualifying[model] = runs
    
    if len(qualifying) < 3:
        return {"error": f"only {len(qualifying)} capable models"}
    
    # Build benefit matrix
    model_benefits = {}
    for model, runs in qualifying.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        benefits = {}
        for tid in common:
            o_p = oracle[tid].get("partial_score", 0) or 0
            f_p = full[tid].get("partial_score", 0) or 0
            benefits[tid] = f_p - o_p
        model_benefits[model] = benefits
    
    # Tasks present in ALL capable models
    common_tasks = set.intersection(*[set(b.keys()) for b in model_benefits.values()])
    if len(common_tasks) < 5:
        # Relax: tasks in at least 80% of models
        from collections import Counter
        task_counts = Counter()
        for b in model_benefits.values():
            task_counts.update(b.keys())
        threshold = int(len(qualifying) * 0.8)
        common_tasks = {t for t, c in task_counts.items() if c >= threshold}
        # Fill missing with 0
        relaxed = True
    else:
        relaxed = False
    
    common_tasks = sorted(common_tasks)
    models = sorted(model_benefits.keys())
    k = len(models)
    n = len(common_tasks)
    
    if n < 5:
        return {"error": f"only {n} common tasks"}
    
    # Build rank matrix (handle missing with median imputation)
    rank_matrix = np.zeros((k, n))
    for i, model in enumerate(models):
        values = []
        for t in common_tasks:
            values.append(model_benefits[model].get(t, 0.0))
        rank_matrix[i] = scipy_stats.rankdata(values)
    
    # Kendall's W
    rank_sums = rank_matrix.sum(axis=0)
    mean_rank_sum = np.mean(rank_sums)
    S = np.sum((rank_sums - mean_rank_sum) ** 2)
    W = 12 * S / (k ** 2 * (n ** 3 - n))
    
    chi2 = k * (n - 1) * W
    df = n - 1
    p_value = 1 - scipy_stats.chi2.cdf(chi2, df)
    
    if W < 0.1: interp = "no agreement"
    elif W < 0.3: interp = "weak agreement"
    elif W < 0.5: interp = "moderate agreement"
    elif W < 0.7: interp = "strong agreement"
    else: interp = "very strong agreement"
    
    # Find consistently helped/hurt tasks
    consistently_helped = []
    consistently_hurt = []
    for j, t in enumerate(common_tasks):
        vals = [model_benefits[m].get(t, 0) for m in models]
        available = [v for m, v in zip(models, vals) if t in model_benefits[m]]
        if len(available) >= k * 0.8:
            if all(v > 0.01 for v in available):
                consistently_helped.append((t, float(np.mean(available))))
            elif all(v < -0.01 for v in available):
                consistently_hurt.append((t, float(np.mean(available))))
    
    consistently_helped.sort(key=lambda x: -x[1])
    consistently_hurt.sort(key=lambda x: x[1])
    
    return {
        "n_models": k,
        "models": models,
        "n_common_tasks": n,
        "relaxed_matching": relaxed if 'relaxed' in dir() else False,
        "kendalls_W": round(float(W), 4),
        "interpretation": interp,
        "chi2": round(float(chi2), 4),
        "p_value": round(float(p_value), 6),
        "significant_005": p_value < 0.05,
        "consistently_team_helped": consistently_helped[:15],
        "consistently_team_hurt": consistently_hurt[:15],
        "n_consistently_helped": len(consistently_helped),
        "n_consistently_hurt": len(consistently_hurt),
    }


def compute_all_bootstrap_cis(model_runs):
    """Bootstrap CIs for all key metrics per model."""
    results = {}
    
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = sorted(set(oracle.keys()) & set(full.keys()))
        
        if len(common) < 10:
            continue
        
        o_passes = [1 if oracle[t].get("pass") else 0 for t in common]
        f_passes = [1 if full[t].get("pass") else 0 for t in common]
        o_partials = [oracle[t].get("partial_score", 0) or 0 for t in common]
        f_partials = [full[t].get("partial_score", 0) or 0 for t in common]
        partial_diffs = [f - o for f, o in zip(f_partials, o_partials)]
        
        # Bootstrap CIs
        oracle_rate_ci = bootstrap_ci(o_passes)
        full_rate_ci = bootstrap_ci(f_passes)
        uplift_ci = bootstrap_pass_rate_diff(o_passes, f_passes)
        partial_improve_ci = bootstrap_ci(partial_diffs)
        
        # Bootstrap CI for odds ratio
        def boot_or(data):
            n = len(data) // 2
            o = data[:n]
            f = data[n:]
            a = sum(f) + 0.5; b = n - sum(f) + 0.5
            c = sum(o) + 0.5; d = n - sum(o) + 0.5
            return (a * d) / (b * c)
        
        combined = o_passes + f_passes
        or_ci = bootstrap_ci(combined, stat_func=boot_or)
        
        # NNT CI (from uplift CI)
        nnt_ci_lower = 1 / uplift_ci[1] if uplift_ci[1] > 0 else None
        nnt_ci_upper = 1 / uplift_ci[0] if uplift_ci[0] > 0 else None
        
        results[model] = {
            "n_tasks": len(common),
            "oracle_rate": round(np.mean(o_passes), 4),
            "oracle_rate_ci95": [round(oracle_rate_ci[0], 4), round(oracle_rate_ci[1], 4)],
            "full_rate": round(np.mean(f_passes), 4),
            "full_rate_ci95": [round(full_rate_ci[0], 4), round(full_rate_ci[1], 4)],
            "uplift": round(np.mean(f_passes) - np.mean(o_passes), 4),
            "uplift_ci95": [round(uplift_ci[0], 4), round(uplift_ci[1], 4)],
            "partial_improvement": round(np.mean(partial_diffs), 4),
            "partial_improvement_ci95": [round(partial_improve_ci[0], 4), round(partial_improve_ci[1], 4)],
        }
    
    return results


def generate_latex_tables(model_runs, bootstrap_results, kendall_result, outdir):
    """Generate publication-ready LaTeX tables."""
    os.makedirs(outdir, exist_ok=True)
    
    # ── Table: Per-Model Collaboration Metrics ──────────────────────
    # Filter to models with meaningful results
    capable = {m: r for m, r in bootstrap_results.items() 
               if r["oracle_rate"] > 0.01 or r["full_rate"] > 0.01}
    
    # Sort by full_rate descending
    sorted_models = sorted(capable.keys(), key=lambda m: -capable[m]["full_rate"])
    
    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\caption{Multi-agent collaboration metrics across models. " +
                 r"McNemar's test evaluates whether team-unique wins significantly exceed oracle-unique wins. " +
                 r"Cohen's $h$ measures effect size of pass rate difference. " +
                 r"NNT = number of tasks needed for one additional pass via teamwork. " +
                 r"$^\dagger$ indicates models below tool-use capability threshold.}")
    lines.append(r"\label{tab:collaboration_metrics}")
    lines.append(r"\resizebox{\textwidth}{!}{%")
    lines.append(r"\begin{tabular}{lcccccccc}")
    lines.append(r"\toprule")
    lines.append(r"Model & $n$ & Oracle & Full (Team) & Uplift [95\% CI] & Cohen's $h$ & OR [95\% CI] & NNT & McNemar $p$ \\")
    lines.append(r"\midrule")
    
    for model in sorted_models:
        r = capable[model]
        runs = model_runs[model]
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        
        # McNemar
        both_pass = sum(1 for t in common if oracle[t].get("pass") and full[t].get("pass"))
        oracle_only = sum(1 for t in common if oracle[t].get("pass") and not full[t].get("pass"))
        full_only = sum(1 for t in common if not oracle[t].get("pass") and full[t].get("pass"))
        b, c = oracle_only, full_only
        if b + c > 0:
            chi2 = (abs(b - c) - 1) ** 2 / (b + c)
            mcn_p = 1 - scipy_stats.chi2.cdf(chi2, df=1)
        else:
            mcn_p = 1.0
        
        # Cohen's h
        p_o = r["oracle_rate"]; p_f = r["full_rate"]
        h = 2 * math.asin(math.sqrt(max(p_f, 0.001))) - 2 * math.asin(math.sqrt(max(p_o, 0.001)))
        
        # Odds Ratio
        n = r["n_tasks"]
        a = int(p_f * n) + 0.5; b_ = n - int(p_f * n) + 0.5
        c_ = int(p_o * n) + 0.5; d_ = n - int(p_o * n) + 0.5
        or_val = (a * d_) / (b_ * c_)
        log_or = math.log(or_val)
        se = math.sqrt(1/a + 1/b_ + 1/c_ + 1/d_)
        or_lo = math.exp(log_or - 1.96 * se)
        or_hi = math.exp(log_or + 1.96 * se)
        
        # NNT
        uplift = r["uplift"]
        nnt = f"{1/uplift:.1f}" if uplift > 0.005 else "---"
        
        # Significance markers
        if mcn_p < 0.001: sig = "***"
        elif mcn_p < 0.01: sig = "**"
        elif mcn_p < 0.05: sig = "*"
        else: sig = ""
        
        # Format model name
        mname = model.replace("_", r"\_")
        
        lines.append(
            f"  {mname} & {r['n_tasks']} & "
            f"{r['oracle_rate']:.1%} & {r['full_rate']:.1%} & "
            f"{r['uplift']:+.1%} [{r['uplift_ci95'][0]:+.1%}, {r['uplift_ci95'][1]:+.1%}] & "
            f"{h:.2f} & "
            f"{or_val:.2f} [{or_lo:.2f}, {or_hi:.2f}] & "
            f"{nnt} & "
            f"{mcn_p:.4f}{sig} \\\\"
        )
    
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}}")
    lines.append(r"\end{table}")
    
    with open(f"{outdir}/table_collaboration_metrics.tex", "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote {outdir}/table_collaboration_metrics.tex")
    
    # ── Table: Assembly Bonus & Shapley ──────────────────────────────
    lines2 = []
    lines2.append(r"\begin{table}[t]")
    lines2.append(r"\centering")
    lines2.append(r"\caption{Role contribution analysis via Shapley value decomposition. " +
                  r"Assembly bonus measures whether full team exceeds best two-role ablation. " +
                  r"Positive interaction indicates superadditivity (synergy).}")
    lines2.append(r"\label{tab:shapley}")
    lines2.append(r"\begin{tabular}{lccccccc}")
    lines2.append(r"\toprule")
    lines2.append(r"Model & $n$ & Full & TNP & TNV & $\phi_P$ & $\phi_V$ & Interaction \\")
    lines2.append(r"\midrule")
    
    for model in sorted_models:
        runs = model_runs[model]
        oracle = get_task_results(runs, "oracle")
        restricted = get_task_results(runs, "restricted")
        full = get_task_results(runs, "full")
        tnp = get_task_results(runs, "team_no_plan")
        tnv = get_task_results(runs, "team_no_verify")
        
        if not all([oracle, restricted, full, tnp, tnv]):
            continue
        
        common = set(oracle.keys()) & set(restricted.keys()) & set(full.keys()) & \
                 set(tnp.keys()) & set(tnv.keys())
        if len(common) < 5:
            continue
        
        n = len(common)
        p = lambda results: sum(1 for t in common if results[t].get("pass")) / n
        
        p_r = p(restricted); p_f = p(full); p_tnp = p(tnp); p_tnv = p(tnv)
        
        shap_p = 0.5 * (p_tnv - p_r) + 0.5 * (p_f - p_tnp)
        shap_v = 0.5 * (p_tnp - p_r) + 0.5 * (p_f - p_tnv)
        interaction = p_f - (p_tnp + p_tnv - p_r)
        
        mname = model.replace("_", r"\_")
        int_marker = "+" if interaction > 0.005 else ("$-$" if interaction < -0.005 else "0")
        
        lines2.append(
            f"  {mname} & {n} & {p_f:.1%} & {p_tnp:.1%} & {p_tnv:.1%} & "
            f"{shap_p:+.3f} & {shap_v:+.3f} & {interaction:+.3f} \\\\"
        )
    
    lines2.append(r"\bottomrule")
    lines2.append(r"\end{tabular}")
    lines2.append(r"\end{table}")
    
    with open(f"{outdir}/table_shapley.tex", "w") as f:
        f.write("\n".join(lines2))
    print(f"  Wrote {outdir}/table_shapley.tex")
    
    # ── Table: Difficulty-Stratified ──────────────────────────────────
    lines3 = []
    lines3.append(r"\begin{table}[t]")
    lines3.append(r"\centering")
    lines3.append(r"\caption{Collaboration benefit stratified by task difficulty (pooled across models). " +
                  r"Hard tasks show significant teamwork benefit; easy tasks show significant overhead.}")
    lines3.append(r"\label{tab:difficulty_stratified}")
    lines3.append(r"\begin{tabular}{lcccccc}")
    lines3.append(r"\toprule")
    lines3.append(r"Difficulty & $n$ & Mean Benefit & 95\% CI & \% Helped & $t$ & $p$ \\")
    lines3.append(r"\midrule")
    
    # Recompute with bootstrap CIs
    task_oracle_rates = defaultdict(list)
    task_full_rates = defaultdict(list)
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        if len(oracle) < 10 or len(full) < 10:
            continue
        for tid, r in oracle.items():
            task_oracle_rates[tid].append(1 if r.get("pass") else 0)
        for tid, r in full.items():
            task_full_rates[tid].append(1 if r.get("pass") else 0)
    
    bins = {
        r"Hard ($\leq$10\%)": (0, 0.1),
        r"Medium (10--50\%)": (0.1, 0.5),
        r"Easy ($>$50\%)": (0.5, 1.01),
    }
    
    for label, (lo, hi) in bins.items():
        benefits = []
        for tid in task_oracle_rates:
            if tid not in task_full_rates:
                continue
            orc_rate = np.mean(task_oracle_rates[tid])
            full_rate = np.mean(task_full_rates[tid])
            if lo <= orc_rate < hi:
                benefits.append(full_rate - orc_rate)
        
        if len(benefits) >= 3:
            benefits = np.array(benefits)
            ci_lo, ci_hi = bootstrap_ci(benefits)
            t_stat, t_p = scipy_stats.ttest_1samp(benefits, 0)
            sig = "***" if t_p < 0.001 else "**" if t_p < 0.01 else "*" if t_p < 0.05 else ""
            pct_helped = np.mean(benefits > 0)
            lines3.append(
                f"  {label} & {len(benefits)} & {np.mean(benefits):+.3f} & "
                f"[{ci_lo:+.3f}, {ci_hi:+.3f}] & {pct_helped:.0%} & "
                f"{t_stat:.2f} & {t_p:.4f}{sig} \\\\"
            )
    
    lines3.append(r"\bottomrule")
    lines3.append(r"\end{tabular}")
    lines3.append(r"\end{table}")
    
    with open(f"{outdir}/table_difficulty_stratified.tex", "w") as f:
        f.write("\n".join(lines3))
    print(f"  Wrote {outdir}/table_difficulty_stratified.tex")
    
    # ── Table: Kendall's W ────────────────────────────────────────────
    if "error" not in kendall_result:
        lines4 = []
        lines4.append(r"\begin{table}[t]")
        lines4.append(r"\centering")
        lines4.append(r"\caption{Cross-model agreement on which tasks benefit from teamwork " +
                      r"(Kendall's $W$ coefficient of concordance). Computed over capable models " +
                      r"(oracle pass rate $\geq$ 3\%).}")
        lines4.append(r"\label{tab:kendalls_w}")
        lines4.append(r"\begin{tabular}{lc}")
        lines4.append(r"\toprule")
        lines4.append(r"Statistic & Value \\")
        lines4.append(r"\midrule")
        lines4.append(f"  Models ($k$) & {kendall_result['n_models']} \\\\")
        lines4.append(f"  Common tasks ($n$) & {kendall_result['n_common_tasks']} \\\\")
        sig = "***" if kendall_result['p_value'] < 0.001 else "**" if kendall_result['p_value'] < 0.01 else "*" if kendall_result['p_value'] < 0.05 else ""
        lines4.append(f"  Kendall's $W$ & {kendall_result['kendalls_W']:.4f} ({kendall_result['interpretation']}) \\\\")
        lines4.append(f"  $\\chi^2$ & {kendall_result['chi2']:.2f} \\\\")
        lines4.append(f"  $p$-value & {kendall_result['p_value']:.4f}{sig} \\\\")
        lines4.append(f"  Consistently helped & {kendall_result['n_consistently_helped']} tasks \\\\")
        lines4.append(f"  Consistently hurt & {kendall_result['n_consistently_hurt']} tasks \\\\")
        lines4.append(r"\bottomrule")
        lines4.append(r"\end{tabular}")
        lines4.append(r"\end{table}")
        
        with open(f"{outdir}/table_kendalls_w.tex", "w") as f:
            f.write("\n".join(lines4))
        print(f"  Wrote {outdir}/table_kendalls_w.tex")


def main():
    results_dir = "/u/ybkim95/TeamBench/shared/ablation_results"
    outdir = "/u/ybkim95/TeamBench/shared/paper"
    
    print("Loading results...")
    model_runs = load_all_results(results_dir)
    
    # Filter to models with oracle+full data >= 10 tasks
    qualifying = {}
    for model, runs in model_runs.items():
        oracle = get_task_results(runs, "oracle")
        full = get_task_results(runs, "full")
        common = set(oracle.keys()) & set(full.keys())
        if len(common) >= 10:
            qualifying[model] = runs
    
    print(f"\n{'='*70}")
    print("1. KENDALL'S W (CAPABLE MODELS ONLY)")
    print(f"{'='*70}")
    kw = capable_models_kendall_w(qualifying, min_oracle_rate=0.03)
    if "error" not in kw:
        print(f"   Models: {kw['n_models']} — {', '.join(kw['models'])}")
        print(f"   Common tasks: {kw['n_common_tasks']}")
        print(f"   W = {kw['kendalls_W']:.4f} ({kw['interpretation']})")
        sig = "***" if kw['p_value'] < 0.001 else "**" if kw['p_value'] < 0.01 else "*" if kw['p_value'] < 0.05 else "ns"
        print(f"   χ²={kw['chi2']:.2f}, p={kw['p_value']:.6f} {sig}")
        print(f"   Consistently helped: {kw['n_consistently_helped']} tasks")
        if kw['consistently_team_helped']:
            for t, v in kw['consistently_team_helped'][:10]:
                print(f"     {t}: +{v:.3f}")
        print(f"   Consistently hurt: {kw['n_consistently_hurt']} tasks")
        if kw['consistently_team_hurt']:
            for t, v in kw['consistently_team_hurt'][:10]:
                print(f"     {t}: {v:.3f}")
    else:
        print(f"   Error: {kw['error']}")
    
    print(f"\n{'='*70}")
    print("2. BOOTSTRAP CONFIDENCE INTERVALS")
    print(f"{'='*70}")
    bootstrap = compute_all_bootstrap_cis(qualifying)
    for model in sorted(bootstrap.keys(), key=lambda m: -bootstrap[m]["full_rate"]):
        r = bootstrap[model]
        print(f"\n   {model} (n={r['n_tasks']}):")
        print(f"     Oracle: {r['oracle_rate']:.1%} [{r['oracle_rate_ci95'][0]:.1%}, {r['oracle_rate_ci95'][1]:.1%}]")
        print(f"     Full:   {r['full_rate']:.1%} [{r['full_rate_ci95'][0]:.1%}, {r['full_rate_ci95'][1]:.1%}]")
        print(f"     Uplift: {r['uplift']:+.1%} [{r['uplift_ci95'][0]:+.1%}, {r['uplift_ci95'][1]:+.1%}]")
        print(f"     Partial: {r['partial_improvement']:+.3f} [{r['partial_improvement_ci95'][0]:+.3f}, {r['partial_improvement_ci95'][1]:+.3f}]")
    
    print(f"\n{'='*70}")
    print("3. GENERATING LATEX TABLES")
    print(f"{'='*70}")
    generate_latex_tables(qualifying, bootstrap, kw, outdir)
    
    # Save all results
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating,)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, np.bool_): return bool(obj)
            return super().default(obj)
    
    combined = {
        "kendalls_w_capable": kw,
        "bootstrap_cis": bootstrap,
    }
    with open(f"{outdir}/collaboration_metrics_v2.json", "w") as f:
        json.dump(combined, f, indent=2, cls=NpEncoder)
    print(f"\n  Saved {outdir}/collaboration_metrics_v2.json")


if __name__ == "__main__":
    main()
