# TeamBench v2 — handoff and replication

Everything needed to continue this work on another machine. Written to be
followed top to bottom with no other context.

Branch: `v2`. Base: `main` @ `d185aef1` (2026-05-18).
Host of record: `matlaberp8:/u/ybkim95/TeamBench`. There is no other copy.

---

## 0. What this branch is

The v1 paper reported that GH-sourced tasks were never solved by any model in
any condition. v2 found out why. It was not
the models. Thirteen defects, all in the benchmark, stacked on top of each other
so that the GitHub-derived half of the corpus could not measure anything at all.

The chain, in the order each one became visible (each was hidden by the one
above it):

| # | Defect | Scale | Fix |
|---|--------|-------|-----|
| 1 | `conftest.py` absent, so pytest cannot resolve fixtures | 541 of 553 tasks with tests | superseded by #11 |
| 2 | package present only in fragments (`No module named 'spacy.util'`) | corpus-wide | superseded by #11 |
| 3 | test-only dependencies absent | corpus-wide | resolve from the failure text |
| 4 | build venv used `--system-site-packages`, so system `attrs`/`pydantic_core` shadowed the checkout | 9 of 73 failures named a system path | sealed venv |
| 5 | fresh venv's bundled pip too old for PEP 660 editable installs | 49 of 110 installs failed | upgrade pip first |
| 6 | FAIL_TO_PASS judged after the patch was applied; `git stash` does not stash untracked files | all | judge on the pristine tree |
| 7 | `pip install -e '.[test]'` returns 0 for an extra that does not exist | all of attrs | read the declared groups, handle PEP 735 |
| 8 | test node ids built by string concatenation; the added test is usually a class method | 24 tasks undecided | resolve ids from `--collect-only` |
| 9 | `requires-python` unmet (home-assistant needs >=3.13.2) | ceiling 26 | fetch standalone CPython 3.13/3.14 |
| 10 | installing dev requirements pulled a RELEASED copy of the library under test over the editable install | 9 jinja tasks flipped to "the fix does not work" | assert the source still wins |
| 11 | **the test that defines the bug is the one the PR adds** | 189 tasks could not discriminate at all; 40 shipped the test in the workspace, handing the agent the answer | stage from `base_sha`, inject the tests at grade time |
| 12 | **the import check loaded a package module as a detached top-level module**, so every relative import raised and no submission could ever pass it | 632 graders; failed with the maintainers' own fix on 37 of 59 staged tasks | import by dotted module name |
| 13 | **the grader inherited the repo's `addopts`**, including `--cov-fail-under=99`, so a single-file run failed on coverage while every test passed | 633 graders; explains arrow 0/9, poetry 0/4, starlette 0/3 | clear `addopts` and `filterwarnings` |

11, 12 and 13 are the ones that mattered. Together they mean the old GH numbers
measured nothing, and that no downgrade of the paper's claims was warranted:
the benchmark was broken, not the finding.

Also fixed: `spec.md` and `brief.md` linked the fix PR by URL in 1061 places,
which turns the task into a memorisation test for any model that has seen
GitHub. SWE-bench withholds the PR for this reason.

---

## 1. Bring up a new machine

### 1.1 Clone

```bash
git clone https://github.com/ybkim95/TeamBench.git
cd TeamBench
git checkout v2
```

### 1.2 Python environment

Requires Python 3.10+ for the harness itself. `uv` is the lockfile of record.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # if uv is absent
uv sync                                            # creates .venv from uv.lock
# or, without uv:
python3 -m venv .venv && .venv/bin/pip install -e .
```

### 1.3 Credentials  (NOT in git, transfer by hand)

`.env` at the repo root. Keys actually used:

```
GEMINI_API_KEY            plus GEMINI_API_KEY_1 .. GEMINI_API_KEY_13 (rotation pool)
OPENAI_API_KEY
ANTHROPIC_API_KEY
GITHUB_TOKEN              needed: the corpus tooling hits the GitHub API heavily
OPENROUTER_API
```

Copy it from `matlaberp8:/u/ybkim95/TeamBench/.env`. It is the canonical copy;
do not use `~/CoDaS_v4/.env`.

There is also an untracked `api_keys.txt` on matlaberp8 holding a GitHub PAT and
one other token, neither duplicated in `.env`. It is referenced by no code.
Decide whether it is still needed; if so fold it into `.env`, then delete it.

### 1.4 Standalone interpreters  (fetched, not committed)

Nine repos declare `requires-python >= 3.11/3.12/3.13/3.14`. Without them their
tasks fail at install for a reason that has nothing to do with the corpus.

```bash
mkdir -p .cache/pythons && cd .cache/pythons
# pick the newest release from astral-sh/python-build-standalone
for v in 3.13.15 3.14.7; do
  tag=20260901
  curl -sSL -o p.tgz \
    "https://github.com/astral-sh/python-build-standalone/releases/download/${tag}/cpython-${v}%2B${tag}-x86_64-unknown-linux-gnu-install_only.tar.gz"
  tar xzf p.tgz && mv python "py${v}" && rm p.tgz
done
cd ../..
.venv/bin/python -c "import sys;sys.path.insert(0,'.');
import importlib.util as u;s=u.spec_from_file_location('b','scripts/build_verified_core.py');
m=u.module_from_spec(s);s.loader.exec_module(m);print(m.available_pythons())"
```

Expect `[((3,14,7),...), ((3,13,15),...), ((3,10,x),...)]`.

On a Mac mini use the `aarch64-apple-darwin` assets instead of
`x86_64-unknown-linux-gnu`. A compiler must be present (`gcc`/`clang` plus
`make`); some test dependencies build C extensions.

### 1.5 Long-running jobs

On a login-shell machine, `nohup`'d jobs die at logout unless lingering is on:

```bash
loginctl show-user "$USER" | grep Linger=yes || sudo loginctl enable-linger "$USER"
```

---


## BLOCKER: the Anthropic credential is invalid (found 2026-09-13)

`ANTHROPIC_API_KEY` in `.env` returns HTTP 401 `authentication_error`. It was
valid earlier the same day and died mid-sweep. There is no second Anthropic
credential on the machine. Everything claude-sonnet-5 is blocked until a fresh
key is in `.env`.

Confirm a key before launching anything that costs hours:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-5","max_tokens":8,"messages":[{"role":"user","content":"hi"}]}'
```

### What this cost, and what now prevents it

The sweep did not stop when the key was rejected. It recorded 68 runs as
zero-score failures and wrote complete-looking output JSONs. Averaged, that
produced a Full Team "raw mean 0.019, disc mean 0.500" at budget 140 from 47
runs that never reached the model plus one that did.

Fixed in three places, all verified:

| Layer | File | Behaviour now |
|---|---|---|
| analysis | `scripts/budget_curve.py`, `scripts/make_figure1.py` | `infrastructure_error()` drops credential/429/5xx rows from every aggregate and both paired tests; prints what it dropped; a fully dead cell reports no statistic |
| collection | `harness/ablation.py` | `_is_credential_failure()` aborts the sweep at the first 401; 429 and 5xx stay transient and keep retrying |
| caching | `scripts/run_budget_sweep.py` | `credential_dead_runs()` refuses to skip a cell whose output contains 401s, so fixing the key actually reruns it |

Regression check: gemini-3-flash output is byte-identical after the change.

### Sonnet sweep status

| Budget | Solo | Full Team | Usable |
|---|---|---|---|
| 20 | 48/48 | 48/48 | yes, the only sound cell |
| 60 | 48/48 | 27/48 | no, 21 dead, contiguous suffix |
| 140 | 48/48 | 1/48 | no, 47 dead |

Budgets 60 and 140 are in
`shared/ablation_results/budget_sweep/core_tasks/quarantine_credential_failure/`
with a README. They are absent from the parent directory so a rerun regenerates
them. Do not read them as results.

At budget 20 Sonnet shows **no team deficit**: Solo and Full Team each solve
4 of 48, paired discriminative delta $+0.000$, discordant pairs 2 each way.
Gemini at the same budget has Full Team at 0/48.


## 2. Where the state lives

| Path | In git | What it is |
|------|--------|------------|
| `harness/`, `scripts/`, `generators/`, `leaderboard/`, `adapters/` | yes | all code |
| `tasks/` | yes, **except GH `workspace/`** | task definitions, specs, briefs, graders, reference patches |
| `shared/paper/quality/` | yes | every measurement this branch produced |
| `shared/paper/human_study/` | yes | de-identified human study artifacts |
| `paper/` | partly | drafts; `paper/comments/` is excluded |
| `.env`, `api_keys.txt` | **no** | credentials, hand-carry |
| `human_eval/` | **no** | participant data, IRB 7676 |
| `.cache/` | **no** | 78 GB: interpreters, per-task dependency venvs, grader backups |
| `.venv/` | **no** | 20 GB |
| `shared/runs/`, `shared/ablation_runs/`, `shared/role_ablation/`, `shared/*_campaign/` | **no** | 130,000+ per-run agent artifacts, regenerated by rerunning |
| `shared/*.json`, `shared/ablation_results/*.json`, `shared/ea_results/*.json` | yes | the consolidated experimental record |
| `paper_old/`, `iterace_feedbacks/`, and the review-correspondence directory | **no** | superseded drafts and correspondence; see .gitignore for the exact paths |

GH task `workspace/` directories are deliberately not committed. They are
fragments of upstream repositories, they are what defect #11 was about, and
vendoring them puts AGPL-3.0, GPL-3.0 and LGPL-3.0 code under this repo's MIT
licence.

Nothing is lost. `tasks/GH*/curation_notes.json` (621 files, carrying `repo` and
`base_sha`) and `tasks/GH*/reference/patch.diff` (631 files) ARE tracked, and
`harness/core_staging.py::stage` reconstructs any workspace by checking the real
repository out at `base_sha`. What that costs: a GH task outside the verified
core has no workspace until it is staged, so a fresh clone can run the
generator-backed and static tasks immediately, and GH tasks only after staging.
`stage()` is gated on `load_core()` today; widening it to any task with
`repo` + `base_sha` in its curation notes is a two-line change when the rest of
the corpus is needed.

### Regenerating what is not in git

```bash
# per-task dependency environments (built on demand, ~1-3 min each)
#   nothing to run: harness/core_staging.py::ensure_deps builds and caches them
# agent runs
.venv/bin/python scripts/run_budget_sweep.py --model gemini-3-flash-preview
```

---

## 3. State of the work, exactly

### 3.1 The corpus ceiling

Computed from the reference patches, no network needed:

```
GH tasks with repo + base_sha + patch      631
patches that ADD a test function           229   (36%)   <- ceiling for test-based verification
```

The other 402 cannot be verified by a test signal because the upstream PR never
added one. They may still discriminate through a grader's non-test checks, which
is a separate measurement (`scripts/discriminative_rescore.py`). Do not conflate
the two.

### 3.2 Verified core

`scripts/build_verified_core.py` checks out each task's upstream at `base_sha`
and asks two questions:

```
G_fail   the tests the patch ADDS fail without the source fix
G_pass   the same tests pass with it
```

Both must hold. Results, newest shard wins, merged by
`harness/core_staging.py::load_core`:

| shard | scope | verified / ceiling |
|-------|-------|--------------------|
| `verified_core_r2.json` | tier 1, 130 tasks | 55 / 77 |
| `verified_core_r4.json` | tier 2, 168 tasks | 6 / 44 |
| `verified_core_tier3.json` | tier 3, 43 tasks | 16 / 32 |
| `verified_core_r3.json` | interpreter-blocked repos, 48 tasks | 3 |
| **merged core** | | **80 tasks, 23 repos, 79 with a pinned env** |

Earlier shards (`_v1_envbug`, `_v2_nodeids`, `_v3`, `verified_core.json`) are
kept only as an audit trail of the defects above. `load_core` prefers any row
that carries `env_freeze`.

### 3.3 Staged validation — the number that matters

`scripts/stage_verified_core.py --all` grades every core task three ways:

```
A  pristine checkout, grader as it stands   should FAIL. If it passes, the grader
                                            cannot see the bug at all.
B  pristine + the PR's tests injected       should FAIL. This is the signal.
C  the maintainers' full fix                should PASS.
```

A task is usable iff B fails and C passes.

```
run 1  (before the import-check fix)   10 usable / 59 graded
run 2  (after it)                      33 usable / 66 graded,  25 blind
run 3  (after the coverage-gate fix)   48 usable / 76 graded,  31 blind   <- current
```

**48 tasks is the current TeamBench-Core.** The ids are in
`shared/paper/quality/core_tasks.json`.

"31 of 76 graders blind without test injection" is the headline defect number:
41% of the graders could not distinguish any two submissions until the held-out
tests were injected.

By repository, run 3:

```
jinja         9/9     marshmallow   4/4     pydantic    3/3
arrow         8/9     celery        4/4     starlette   3/3
aiohttp       5/8     redis-py      4/6     attrs       1/2
werkzeug      5/7     narwhals      1/4     mlflow      1/3
poetry        0/4     mitmproxy     0/2     (13 repos at 0/1)
```

Still failing with the reference fix applied: C1 21, C5 12, C11 5, C9 3, C3 1.
Those 28 are the next thing to look at; poetry 0/4 is the largest single block.

**Check `shared/paper/quality/core_staged.json` first thing.** If it is complete,
run:

```bash
.venv/bin/python - <<'PY'
import json, collections
rows = json.load(open("shared/paper/quality/core_staged.json"))
ok = [r for r in rows if r.get("status") == "ok"]
print("graded %d  usable %d  blind-without-injection %d" % (
    len(ok), sum(1 for r in ok if r.get("usable")),
    sum(1 for r in ok if r.get("grader_blind_without_injection"))))
c = collections.Counter()
for r in ok:
    if not r.get("usable"):
        for x in r["C"].get("failed") or []: c[x] += 1
print("still failing with the reference fix:", dict(c.most_common(6)))
PY
```

If it is incomplete or absent, rerun it (deps are cached, so this is much faster
the second time):

```bash
.venv/bin/python -u scripts/stage_verified_core.py --all \
  --dest /tmp/staged --workers 4 --timeout 2400 \
  --out shared/paper/quality/core_staged.json
```

---

## 4. The next four steps, in order

### Step 1 — DONE. The core is 48 tasks (above)

Already written: `shared/paper/quality/core_tasks.json` holds the 48 usable
ids. Regenerate it after any rerun with:

```bash
.venv/bin/python - <<'PY'
import json
rows = json.load(open("shared/paper/quality/core_staged.json"))
sel = sorted(r["task"] for r in rows if r.get("usable"))
json.dump({"selected_flat": sel}, open("shared/paper/quality/core_tasks.json", "w"), indent=1)
print(len(sel), "tasks ->", "shared/paper/quality/core_tasks.json")
PY
```

### Step 2 — DONE. The do-nothing floor on staged tasks

`shared/paper/quality/pristine_checks.json` was computed against the OLD
fragment workspaces. It is stale for every core task. The discriminative rescore
depends on it.

`scripts/core_pristine_baseline.py` establishes it through the real runtime
path (`harness.run_all.setup_run` + `grade_run`), so the baseline is what the
benchmark actually produces rather than a reimplementation. Result, in
`shared/paper/quality/pristine_checks_core.json`:

```
baselined                                    48 / 48
mean do-nothing partial (raw scale)          0.815
tasks an empty submission already PASSES     0
tasks with NO discriminative check           0

checks across the core                       374
guards (pass on an untouched workspace)      303   (81%)
discriminative                                71
discriminative per task            median 1, max 4
```

81% of every reported partial_score was credit for not vandalising the
workspace. The guard fraction and the 0.815 floor agree, which is the internal
consistency check.

A check counts as discriminative for a task iff it fails on that task's pristine
workspace. That is per (task, check), never per check name: "source modules
import without error" is a guard on one task and the entire point of another.

Rerun with:

```bash
.venv/bin/python -u scripts/core_pristine_baseline.py --workers 4
```

### Step 3 — DONE. The compute-matched budget curve

This is what the whole diagnosis chain was unblocking. The previous attempt
returned binary pass 0 of 100, which defects 11, 12 and 13 fully explain.

```bash
.venv/bin/python -u scripts/run_budget_sweep.py \
  --model gemini-3-flash-preview \
  --tasks-file shared/paper/quality/core_tasks.json \
  --budgets 20 60 140
```

Solo and Full Team at identical `total_turns`, enforced by the shared
`TurnBudget` in `harness/agent_loop.py`. Every published v1 comparison ran Solo
at 20 turns against Full Team at up to 140, so any difference was confounded
with a 7x compute gap.

Output goes to `shared/ablation_results/budget_sweep/core_tasks/`, namespaced by
the selection so it can never be silently mixed with an older sweep.

Read it with `scripts/budget_curve.py`. Result over 288 runs, 48 tasks, one
model (gemini-3-flash-preview), seed 0:

```
budget  condition    n   pass         raw mean  disc mean  guard violations
  20    Solo        48   4/48    8%     0.826     0.104          1
  20    Full Team   48   0/48    0%     0.803     0.000          1
  60    Solo        48   5/48   10%     0.839     0.149          2
  60    Full Team   48   0/48    0%     0.793     0.031          4
 140    Solo        48  10/48   21%     0.841     0.267          3
 140    Full Team   48   2/48    4%     0.779     0.080          8
```

Paired, same task and same budget:

```
budget  20   team-only wins 0,  solo-only 4    mean disc delta -0.104
budget  60   team-only wins 0,  solo-only 5    mean disc delta -0.118
budget 140   team-only wins 1,  solo-only 9    mean disc delta -0.188

19 discordant pairs (team 1, solo 18); exact two-sided sign test p = 7.6e-05
```

Three things this says that the v1 setup could not have said.

1. **At equal compute the team does not win.** Across 144 paired comparisons the
   team solved exactly one task the solo agent failed, GH35_jinja_1665 at 140
   turns.
2. **The gap widens with budget** (-0.104, -0.118, -0.188), so "the team needs
   more compute" is not the explanation. More compute makes it relatively worse.
3. **The team breaks things more often, increasingly so.** Guard violations, a
   submission that deleted tests or wiped a file, go 1/48 -> 4/48 -> 8/48 for the
   team against 1 -> 2 -> 3 for solo. At 140 turns 17% of team runs damaged the
   workspace against 6% of solo runs.

And the scale decides whether any of this is visible at all:

```
             budget 20   budget 60   budget 140
raw   Solo      0.826       0.839       0.841     +1.5 points
raw   Team      0.803       0.793       0.779     -2.4 points
disc  Solo      0.104       0.149       0.267     2.6x
disc  Team      0.000       0.031       0.080
```

On the raw scale a 7x compute increase moves nothing and the conditions sit on
top of each other, because 81% of the checks are guards and everything is
compressed against the ceiling. That is the scale the v1 numbers were on.

Caveat that a reviewer will raise first: **one model, one seed.** The sign test
is over task-to-task variation, not over model or seed variation. A second model
is the largest remaining gap.

### Step 4 — DONE. The admission gate on the core

```bash
TASKS=$(.venv/bin/python -c "import json;print(' '.join(json.load(open('shared/paper/quality/core_tasks.json'))['selected_flat']))")
TEAMBENCH_RUNS_DIR=/tmp/tb_gate .venv/bin/python -u scripts/task_admission_gate.py \
  --bootstrap --tasks $TASKS --reference-sample 48 --workers 3
```

`--bootstrap` is required: the gate refuses to run under the repository venv.
Result, in `shared/paper/quality/admission_core_summary.json`:

```
G1  48/48      an empty submission scores 0 on the discriminative checks
G2  48/48      the pristine workspace does not pass
G3  47/48      the upstream reference scores 1.0
G4  48/48
G5  48/48
G6   1/48      >=50% of checks discriminative   (measured median 0.14)
G7  48/48

raw floor mean 0.8146   (matches Step 2's independent 0.815)
G3 failure: GH17_aiohttp_10151
```

**G6 is left failing on purpose.** Lowering its threshold would admit 46 tasks
immediately, and satisfying it as written would mean deleting anti-cheat checks
that legitimately detect deleted tests, wiped files and cheat markers. The
concern G6 was built for is real (303 of 374 checks are guards) but the remedy
belongs in scoring, not in the corpus: exclude guards from the score. So the
gate suite now separates two things it used to conflate.

```
validity      can the task distinguish submissions?   G1+G2+G3 -> yes, 47/48
granularity   how finely?                             G6 -> coarsely, median 1 check
```

That granularity number is itself a finding: with a median of one discriminative
check per task, TeamBench-Core is effectively pass/fail, and the graded partial
credit the v1 paper reported was 81% guard mass.

Three defects in the gate had to be fixed before any of this meant anything;
they are in the commit for `harness/reference_apply.py` and
`scripts/task_admission_gate.py`. Briefly: `invoke_grader` was a copy of
`grade_run` that had drifted and graded staged tasks without restoring the
held-out tests; G3 built its reference workspace from the vendored fragment via
reparameterisation machinery that has no meaning for an upstream checkout, and
scored the reference 0.71 where a direct `git apply` scores 1.0; and G1 required
a raw floor of exactly 0.0, which no task with a guard check can reach.

---

## 5. Open items, honestly listed

- **home-assistant: 0 of a ceiling of 19.** `requires-python` is satisfied now,
  but its pinned `lru-dict` and `ciso8601` do not build on 3.13/3.14 and one
  commit pins `home-assistant-bluetooth==1.12.1`, which is not on PyPI. A
  `--no-deps` fallback is in place and did not rescue it. ~700 pinned
  dependencies; judged not worth the ceiling.
- **COMPILED repos held back**: numpy, scipy, pandas, matplotlib, scikit-learn,
  statsmodels, spaCy, pytorch, ray, psycopg, pymc. 165 tasks, ceiling 53. They
  build their own extensions; a half-built extension reproduces exactly the
  import errors this work removes. Needs a build image.
- **GIANT repos held back**: transformers, keras, pytorch-lightning, gpytorch,
  autogluon, darts, airflow. 94 tasks, ceiling 23. Installs pull torch or
  tensorflow.
- **psycopg dropped outright.** `from psycopg import pq` needs the compiled
  companion and its suite wants a live PostgreSQL. Not a corpus defect; not
  testable in a network-isolated container.
- **Residual answer leak**: the task id ends in the PR number
  (`GH140_marshmallow_2874`). Renaming 650 directories would invalidate every
  recorded result and run path, so it is recorded rather than fixed. Weaker than
  a URL: the model has to resolve it unaided.
- **185 of 821 graders hand-roll `score.json`** and emit no checklist, so their
  runs cannot be rescored discriminatively. All non-GH.
- **One model, one seed.** Every curve so far is gemini-3-flash-preview at
  seed 0. A second model and multiple seeds are required before any of this is
  publishable.
- **Firebase RTDB rules are prepared but not deployed**
  (`shared/paper/human_study/database.rules.json`). Deny-by-default. Needs the
  account owner. No effect on the paper.
- **Paper not yet rewritten.** The v1 manuscript under `paper/` still contains
  the withdrawn v1 claims verbatim: 3.6x at line 1282, the 0.21 relay figure at 476
  and 1212, container enforcement in the Table 7 caption, and the pre-regrade
  human table. The abstract at line 178 still says no single agent can complete
  the task alone while Solo reaches 35.6%.

---

## 6. Reference: what each script does

| Script | Purpose |
|--------|---------|
| `scripts/build_verified_core.py` | check out upstream at `base_sha`, decide G_fail/G_pass, record a pinned `env_freeze`. `--pure-python --tier2 --tier3 --repos --tasks --list-repos` |
| `scripts/stage_verified_core.py` | stage a core task and grade it three ways (A/B/C). `--task` or `--all` |
| `harness/core_staging.py` | the staging the harness itself uses: clone, dependency venv, hold out the tests, restore them at grade time |
| `scripts/fix_import_check.py` | rewrite the graders' import check to import by module name (defect #12) |
| `scripts/fix_pytest_invocation.py` | clear the repo's `addopts`/`filterwarnings` in grader pytest calls (defect #13) |
| `scripts/strip_pr_pointer.py` | remove links to the fix PR from specs and briefs |
| `scripts/fetch_missing_conftest.py` | restore missing `conftest.py` (defect #1; superseded by staging, kept for the record) |
| `scripts/discriminative_rescore.py` | separate guard checks from checks a solution can actually move |
| `scripts/run_budget_sweep.py` | the compute-matched Solo vs Full Team curve |
| `scripts/task_admission_gate.py` | admission gates G1-G7 |

Grader rewrites keep backups under `.cache/grader_backup/` and
`.cache/grader_backup_pytest/`; document rewrites under `.cache/doc_backup/`.
Those are local only. The committed graders are the rewritten ones.

---

## 7. External services

| Service | Where | Note |
|---------|-------|------|
| HuggingFace dataset | `ybkim95/teambench` | mirror lacks the GH tasks |
| HF Space | `ybkim95/teambench-leaderboard` | |
| Website | `teambench/teambench.github.io` | |
| Human study backends | DigitalOcean droplets `152.42.204.136`, `165.227.93.53` | production, not matlaber |
| Firebase RTDB | human study responses | rules not yet applied |
