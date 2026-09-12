#!/usr/bin/env python3
"""
TeamBench Statistical Robustness Analyses
==========================================
Five analyses for the paper methods/results section:
  1. Multi-seed significance (paired bootstrap, seeds 0+1+2 pooled)
  2. Effect size reporting (Cohen's d + practical significance)
  3. Holm-Bonferroni correction (m=15 tests)
  4. Power analysis (MDE at alpha=0.05, power=0.80)
  5. Inter-seed variance and ICC(1,1)

Output: shared/paper/statistical_robustness.json
"""

import json, os, warnings
import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import datetime

warnings.filterwarnings("ignore")

BASE = os.path.join(os.path.dirname(__file__), "..", "shared", "ablation_results")
PAPER = os.path.join(os.path.dirname(__file__), "..", "shared", "paper")

# ── helpers ────────────────────────────────────────────────────────────────────

def normalize_run(r):
    score = int(bool(r["pass"])) if "pass" in r else int(r.get("partial_score", 0) >= 1.0)
    return {"task_id": r.get("task_id",""), "condition": r.get("condition",""),
            "seed": r.get("seed", -1), "score": score}

def load_json_runs(path):
    with open(path) as f:
        d = json.load(f)
    return d if isinstance(d, list) else d.get("runs", [])

def paired_bootstrap(a, b, n_boot=5000, seed=42):
    rng = np.random.default_rng(seed)
    diffs = np.asarray(a) - np.asarray(b)
    obs = diffs.mean()
    n = len(diffs)
    boots = np.array([(diffs[rng.integers(0, n, n)]).mean() for _ in range(n_boot)])
    ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
    boots_h0 = boots - obs
    p = 2 * min(np.mean(boots_h0 >= abs(obs)), np.mean(boots_h0 <= -abs(obs)))
    return obs, max(p, 1/n_boot), ci_low, ci_high

def one_sample_bootstrap(vals, n_boot=5000, seed=42):
    rng = np.random.default_rng(seed)
    vals = np.asarray(vals); obs = vals.mean(); n = len(vals)
    centered = vals - obs
    boots = np.array([centered[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    ci = np.percentile(vals[rng.integers(0, n, (n_boot, n))].mean(axis=1), [2.5, 97.5])
    p = 2 * min(np.mean(boots >= abs(obs)), np.mean(boots <= -abs(obs)))
    return obs, max(p, 1/n_boot), ci[0], ci[1]

def cohens_d(a, b):
    diffs = np.asarray(a) - np.asarray(b)
    return diffs.mean() / (diffs.std(ddof=1) + 1e-12)

def interpret_d(d):
    ad = abs(d)
    return "large" if ad >= 0.8 else ("medium" if ad >= 0.5 else ("small" if ad >= 0.2 else "negligible"))

def compute_icc_one_way(mat):
    mat = np.asarray(mat, float); n, k = mat.shape
    grand = mat.mean()
    SS_b = k * ((mat.mean(axis=1) - grand) ** 2).sum()
    SS_w = ((mat - mat.mean(axis=1, keepdims=True)) ** 2).sum()
    MS_b = SS_b / (n - 1); MS_w = SS_w / (n * (k - 1))
    icc = (MS_b - MS_w) / (MS_b + (k - 1) * MS_w)
    return icc, MS_b, MS_w

def holm_bonferroni(tests, alpha=0.05):
    m = len(tests)
    out = sorted(tests, key=lambda x: x["p"])
    stop = False
    for i, t in enumerate(out):
        threshold = alpha / (m - i)
        t["holm_rank"] = i + 1
        t["holm_threshold"] = round(threshold, 6)
        t["survives_correction"] = (not stop) and (t["p"] <= threshold)
        if not t["survives_correction"]: stop = True
    return out

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

# ── load data ──────────────────────────────────────────────────────────────────

# Phase3 (seeds 1,2)
with open(os.path.join(BASE, "phase3_all_consolidated.json")) as f:
    phase3 = json.load(f)
p3_tasks = set(r["task_id"] for r in phase3["runs"])
all_runs = [normalize_run(r) for r in phase3["runs"]]

# Seed-0 batch files
batch_files = [
    "batch1_swe_data_seed0_g3flash.json", "batch2_sec_policy_neg_seed0_g3flash.json",
    "batch3_inc_ops_seed0_g3flash.json",  "batch4_test_spec_cr_seed0_g3flash.json",
    "batch5_lh_pipe_ir_multi_int_seed0_g3flash.json",
    "batch6_trap_cross_crypto_dist_go_js_seed0_g3flash.json",
    "batch3_full_retry_g3flash.json", "batch5_full_retry_g3flash.json",
    "batch6_full_503_retry.json", "batch6_retry_g3flash.json",
    "crypto_dist_g3flash.json", "crossmodel_g3flash_seed0.json",
]
for fname in batch_files:
    fpath = os.path.join(BASE, fname)
    if os.path.isfile(fpath):
        for r in load_json_runs(fpath):
            if r.get("task_id") in p3_tasks and r.get("seed") == 0:
                all_runs.append(normalize_run(r))

df = pd.DataFrame(all_runs).drop_duplicates(subset=["task_id","seed","condition"], keep="first")
p3_df = df[df["task_id"].isin(p3_tasks)]

# 147-task regression CSV
reg_df = pd.read_csv(os.path.join(PAPER, "task_regression_data.csv"))
reg_df["team_no_plan_score"]   = reg_df["full"] - reg_df["plan_value"]
reg_df["team_no_verify_score"] = reg_df["full"] - reg_df["verify_value"]

CONDS = ["full","oracle","team_no_verify","team_no_plan","restricted"]
COMPARISONS = [("full","oracle"),("full","team_no_plan"),("full","team_no_verify"),
               ("full","restricted"),("team_no_verify","oracle")]

# Build score matrix (task-level mean over seeds)
tasks_all = set(p3_tasks)
for c in CONDS:
    tasks_all &= set(p3_df[p3_df["condition"]==c]["task_id"])
score_mat = pd.DataFrame({
    c: p3_df[p3_df["condition"]==c].groupby("task_id")["score"].mean().reindex(sorted(tasks_all))
    for c in CONDS
}).dropna()

# ── Analysis 1 ────────────────────────────────────────────────────────────────
a1 = {}
for ca, cb in COMPARISONS:
    obs, p, ci_l, ci_h = paired_bootstrap(score_mat[ca].values, score_mat[cb].values)
    a1[f"{ca} vs {cb}"] = {"diff_pp": round(obs*100,3), "ci_95_low_pp": round(ci_l*100,3),
                            "ci_95_high_pp": round(ci_h*100,3), "p_value": round(p,6),
                            "significant_0.05": bool(p < 0.05), "n_tasks": len(score_mat)}
per_seed = {}
for sv in [0,1,2]:
    sd = p3_df[p3_df["seed"]==sv]
    common = sorted(set(sd[sd["condition"]=="full"]["task_id"]) & set(sd[sd["condition"]=="oracle"]["task_id"]) & tasks_all)
    fs = sd[sd["condition"]=="full"].set_index("task_id")["score"].reindex(common).dropna()
    os_ = sd[sd["condition"]=="oracle"].set_index("task_id")["score"].reindex(common).dropna()
    valid = fs.index.intersection(os_.index)
    if len(valid) >= 5:
        obs, p, ci_l, ci_h = paired_bootstrap(fs.loc[valid].values, os_.loc[valid].values)
        per_seed[str(sv)] = {"diff_pp": round(obs*100,3), "p": round(p,6), "n": len(valid)}
a1["seed_stability"] = per_seed

# ── Analysis 2 ────────────────────────────────────────────────────────────────
N147 = 147
a2 = {}
for ca, cb in COMPARISONS:
    a, b = score_mat[ca].values, score_mat[cb].values
    d = cohens_d(a, b)
    obs = (a-b).mean()
    a2[f"{ca} vs {cb}"] = {"cohens_d": round(d,4), "interpretation": interpret_d(d),
                            "diff_pp": round(obs*100,3),
                            "practical_tasks_on_147": round(obs*N147,2),
                            "practical_tasks_on_39": round(obs*len(score_mat),2)}
f147, o147 = reg_df["full"].values, reg_df["oracle"].values
obs147, p147, cl147, ch147 = paired_bootstrap(f147, o147)
d147 = cohens_d(f147, o147)
a2["full_vs_oracle_147tasks_seed0"] = {"n":147,"diff_pp":round(obs147*100,3),
    "cohens_d":round(d147,4),"interpretation":interpret_d(d147),
    "p_value":round(p147,6),"ci_95_low_pp":round(cl147*100,3),"ci_95_high_pp":round(ch147*100,3),
    "tasks_solved_uplift":round(obs147*147,2)}

# ── Analysis 3 ────────────────────────────────────────────────────────────────
all_tests = []
pairs_147 = [("full","oracle",f147,o147),
             ("full","team_no_plan",f147,reg_df["team_no_plan_score"].values),
             ("full","team_no_verify",f147,reg_df["team_no_verify_score"].values),
             ("team_no_verify","oracle",reg_df["team_no_verify_score"].values,o147)]
for ca,cb,a,b in pairs_147:
    obs,p,cl,ch = paired_bootstrap(a,b)
    all_tests.append({"group":"A_conditions","label":f"A: {ca} vs {cb} (n=147)",
                       "p":p,"diff_pp":round(obs*100,3)})
obs,p,cl,ch = paired_bootstrap(score_mat["full"].values, score_mat["restricted"].values)
all_tests.append({"group":"A_conditions","label":"A: full vs restricted (n=39, multi-seed)",
                   "p":p,"diff_pp":round(obs*100,3)})
for cat in ["testing","github_real","multi_layer","pipeline","cross_system"]:
    mask = reg_df["category"]==cat; n_c = mask.sum()
    if n_c >= 3:
        obs,p,cl,ch = one_sample_bootstrap(reg_df.loc[mask,"uplift"].values)
        all_tests.append({"group":"B_categories","label":f"B: uplift in {cat} (n={n_c})",
                           "p":p,"diff_pp":round(obs*100,3),"n":int(n_c)})
reg_s = reg_df.sort_values("oracle").reset_index(drop=True); n=len(reg_s); qs=n//5
for qi in range(5):
    sl = slice(qi*qs,(qi+1)*qs if qi<4 else n)
    obs,p,cl,ch = one_sample_bootstrap(reg_s.iloc[sl]["uplift"].values)
    om = reg_s.iloc[sl]["oracle"].mean()
    all_tests.append({"group":"C_quintiles","label":f"C: Q{qi+1}_uplift (oracle={om:.2f})",
                       "p":p,"diff_pp":round(obs*100,3)})
a3 = {"method":"Holm-Bonferroni (step-down)","m_total_tests":len(all_tests),"alpha":0.05,
      "tests":holm_bonferroni(all_tests),
      "surviving_labels":[t["label"] for t in holm_bonferroni(all_tests) if t["survives_correction"]]}

# ── Analysis 4 ────────────────────────────────────────────────────────────────
diffs = f147 - o147; n=len(diffs)
std_d = diffs.std(ddof=1); mean_d = diffs.mean()
z_a2 = norm.ppf(0.975); z_b = norm.ppf(0.80)
d_mde = (z_a2+z_b)/np.sqrt(n); mde_pp = d_mde*std_d
d_obs = mean_d/std_d; pow_obs = norm.cdf(abs(d_obs)*np.sqrt(n)-z_a2)
a4 = {"n_tasks":n,"alpha":0.05,"desired_power":0.80,
      "observed_mean_diff_pp":round(mean_d*100,3),"observed_std_diff_pp":round(std_d*100,3),
      "observed_cohens_d":round(d_obs,4),"mde_cohens_d":round(d_mde,4),
      "mde_pp":round(mde_pp*100,2),"achieved_power_at_observed_effect":round(pow_obs,4),
      "conclusion":f"With n={n} tasks and stdev={std_d*100:.1f}pp, the study is powered to detect effects of >= {mde_pp*100:.1f}pp at p<0.05 with 80% power."}

# ── Analysis 5 ────────────────────────────────────────────────────────────────
a5 = {}
for cond in CONDS:
    cd = p3_df[p3_df["condition"]==cond]
    fc = cd.groupby("task_id")["seed"].nunique(); fc_tasks = fc[fc==3].index.tolist()
    if len(fc_tasks) < 5: continue
    piv = cd[cd["task_id"].isin(fc_tasks)].pivot_table(index="task_id",columns="seed",values="score",aggfunc="mean").dropna()
    mat = piv.values; sm = mat.mean(axis=0); ss = mat.std(axis=0,ddof=1)
    wv = mat.var(axis=1,ddof=1).mean()
    icc, ms_b, ms_w = compute_icc_one_way(mat)
    interp = "excellent" if icc>=0.75 else ("good" if icc>=0.60 else ("moderate" if icc>=0.40 else "poor"))
    a5[cond] = {"n_tasks_all_3_seeds":len(piv),
                "seed_means":{str(int(s)):round(float(sm[i]),4) for i,s in enumerate(sorted(piv.columns))},
                "mean_within_task_variance":round(float(wv),6),
                "icc_1_1":round(float(icc),4),"icc_interpretation":interp}

# ── Save ──────────────────────────────────────────────────────────────────────
out = {
    "generated_at": datetime.utcnow().isoformat()+"Z",
    "description": "Statistical robustness analyses for TeamBench paper",
    "analysis_1_multiseed_significance": {"n_tasks":len(score_mat),"seeds":"0+1+2 pooled","comparisons":a1},
    "analysis_2_effect_sizes": {"cohens_d_scale":{"negligible":"<0.2","small":"0.2-0.5","medium":"0.5-0.8","large":">0.8"},"results":a2},
    "analysis_3_holm_bonferroni": a3,
    "analysis_4_power_analysis": a4,
    "analysis_5_interseed_variance": {"icc_scale":{"poor":"<0.4","moderate":"0.4-0.6","good":"0.6-0.75","excellent":">0.75"},"results":a5},
}
os.makedirs(PAPER, exist_ok=True)
with open(os.path.join(PAPER, "statistical_robustness.json"), "w") as f:
    json.dump(out, f, indent=2, cls=NumpyEncoder)
print("Done. Results saved to shared/paper/statistical_robustness.json")
