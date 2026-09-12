#!/usr/bin/env bash
# Single bootstrap entrypoint for resuming TeamBench LB100 reruns on any cluster.
#
# Usage:
#   ./scripts/lb100_bootstrap.sh check               # verify environment only
#   ./scripts/lb100_bootstrap.sh sync <SRC>          # rsync checkpoints from <SRC> (e.g. user@host:/path/TeamBench)
#   ./scripts/lb100_bootstrap.sh api                 # launch all API model resumes (Anthropic/OpenAI/Gemini)
#   ./scripts/lb100_bootstrap.sh oss                 # launch full OSS sweep (18 models, sequential)
#   ./scripts/lb100_bootstrap.sh qwen                # launch only Qwen models from OSS sweep (subset of `oss`)
#   ./scripts/lb100_bootstrap.sh status              # show current LB100 dashboard
#   ./scripts/lb100_bootstrap.sh regrade <ckpt>      # race-safe regrade of one checkpoint
#
# Env overrides:
#   TEAMBENCH_VENV     — Python venv with anthropic+openai+google.genai (default: ./venv)
#   CONDA_ENV          — vLLM conda env name (default: vllm-qwen)
#   CONDA_BASE         — Conda install root for OSS (default: /u/ybkim95/zhiyuan/miniconda3)

set -uo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"

TEAMBENCH_VENV="${TEAMBENCH_VENV:-$REPO/venv}"
CONDA_ENV="${CONDA_ENV:-vllm-qwen}"
CONDA_BASE="${CONDA_BASE:-/u/ybkim95/zhiyuan/miniconda3}"
LOGS="$REPO/logs"
RESULTS="$REPO/shared/ablation_results"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOGS" "$RESULTS"

red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
bold()   { printf "\033[1m%s\033[0m\n" "$*"; }

check_harness_fixes() {
    local ok=1
    bold "=== harness fix markers ==="
    if grep -q '"2.5-pro" in self.model' harness/gemini_adapter.py 2>/dev/null; then
        green "  [ok] gemini_adapter: 2.5-pro thinking_budget=0"
    else
        red   "  [missing] gemini_adapter: 2.5-pro fix"; ok=0
    fi
    if grep -q '"thought", False' harness/gemini_adapter.py 2>/dev/null; then
        green "  [ok] gemini_adapter: thought-part filter"
    else
        red   "  [missing] gemini_adapter: thought filter"; ok=0
    fi
    if grep -q '"\.\./submission/attestation\.json"' harness/ablation.py 2>/dev/null; then
        green "  [ok] ablation: restricted prompt uses ../submission/"
    else
        red   "  [missing] ablation: restricted prompt fix"; ok=0
    fi
    if grep -q "max(max_turns, 30)" harness/ablation.py 2>/dev/null; then
        green "  [ok] ablation: restricted max_turns >= 30"
    else
        red   "  [missing] ablation: restricted max_turns bump"; ok=0
    fi
    if grep -q "os.path.normpath" harness/agent_interface.py 2>/dev/null; then
        green "  [ok] agent_interface: WriteFileTool path normalization"
    else
        red   "  [missing] agent_interface: path normalization"; ok=0
    fi
    if grep -q "latest_by_key" harness/ablation.py 2>/dev/null; then
        green "  [ok] ablation: checkpoint dedupe by latest entry"
    else
        red   "  [missing] ablation: checkpoint dedupe"; ok=0
    fi
    if [ -x "scripts/regrade_lb100_checkpoint_safe.py" ]; then
        green "  [ok] safe regrade script present"
    else
        yellow "  [warn] safe regrade script missing — won't be able to fix grader timeouts"
    fi
    return $((1 - ok))
}

check_api_env() {
    local ok=1
    bold "=== API env ==="
    if [ ! -x "$TEAMBENCH_VENV/bin/python3" ]; then
        red "  [missing] python venv at $TEAMBENCH_VENV"; return 1
    fi
    "$TEAMBENCH_VENV/bin/python3" -c "import anthropic" 2>/dev/null \
        && green "  [ok] anthropic" || { red   "  [missing] anthropic in venv"; ok=0; }
    "$TEAMBENCH_VENV/bin/python3" -c "import openai" 2>/dev/null \
        && green "  [ok] openai" || { red   "  [missing] openai in venv"; ok=0; }
    "$TEAMBENCH_VENV/bin/python3" -c "import google.genai" 2>/dev/null \
        && green "  [ok] google.genai" || { red   "  [missing] google.genai in venv"; ok=0; }
    if [ -f .env ]; then
        green "  [ok] .env present"
        for k in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY; do
            grep -q "^$k\|^${k}1" .env && green "    has $k" || yellow "    no $k (resumes for that provider will fail)"
        done
    else
        yellow "  [warn] no .env — keys must be in shell env"
    fi
    return $((1 - ok))
}

check_oss_env() {
    bold "=== OSS env ==="
    if [ ! -d "$CONDA_BASE" ]; then
        red "  [missing] conda base $CONDA_BASE"; return 1
    fi
    if [ ! -d "$CONDA_BASE/envs/$CONDA_ENV" ]; then
        red "  [missing] conda env $CONDA_BASE/envs/$CONDA_ENV"; return 1
    fi
    local CONDA_PY="$CONDA_BASE/envs/$CONDA_ENV/bin/python"
    if [ ! -x "$CONDA_PY" ]; then
        red "  [missing] python in $CONDA_ENV"; return 1
    fi
    # vllm import is slow (loads torch); just check the package dir
    if [ -d "$CONDA_BASE/envs/$CONDA_ENV/lib"/python*/site-packages/vllm ]; then
        green "  [ok] vllm package present in $CONDA_ENV"
    else
        red "  [missing] vllm package in $CONDA_ENV"; return 1
    fi
    if command -v nvidia-smi > /dev/null; then
        local gpus; gpus=$(nvidia-smi -L 2>/dev/null | wc -l)
        green "  [ok] $gpus GPUs visible"
    else
        red "  [missing] nvidia-smi"; return 1
    fi
    return 0
}

cmd_check() {
    check_harness_fixes
    local h=$?
    check_api_env
    local a=$?
    check_oss_env
    local o=$?
    bold "=== summary ==="
    [ $h -eq 0 ] && green "  harness fixes: present" || red "  harness fixes: MISSING (do not run)"
    [ $a -eq 0 ] && green "  API env: ok" || yellow "  API env: degraded (some providers will fail)"
    [ $o -eq 0 ] && green "  OSS env: ok" || yellow "  OSS env: degraded (cannot run OSS)"
    return 0
}

cmd_sync() {
    local src="${1:-}"
    if [ -z "$src" ]; then
        red "usage: $0 sync <user@host:/path/TeamBench>"
        return 2
    fi
    bold "=== rsync checkpoints from $src ==="
    rsync -av --partial --progress \
        "$src/shared/ablation_results/lb100_*.json" \
        "$src/shared/ablation_results/lb100_*.json.checkpoint.jsonl" \
        "$RESULTS/" \
        || { red "rsync failed"; return 1; }
    green "Sync complete. Inspect with: $0 status"
}

launch_api_jobs() {
    local PY="$TEAMBENCH_VENV/bin/python3"
    local stagger=0
    declare -a SPECS=(
        "haiku45|claude-haiku-4-5-20251001|restricted team_no_plan team_no_verify|lb100_haiku45_3cond_seed0.json"
        "sonnet46|claude-sonnet-4-6|restricted team_no_plan team_no_verify|lb100_sonnet46_3cond_seed0.json"
        "gpt54|gpt-5.4|restricted team_no_plan team_no_verify|lb100_gpt54_3cond_seed0.json"
        "gpt5nano|gpt-5.4-nano|restricted team_no_plan team_no_verify|lb100_gpt5nano_3cond_seed0.json"
        "g31lite|gemini-3.1-flash-lite-preview|restricted team_no_plan team_no_verify|lb100_g31lite_3cond_seed0.json"
        "g3flash|gemini-3-flash-preview|restricted team_no_plan team_no_verify|lb100_g3flash_3cond_seed0.json"
        "gemini-3.1-pro-preview|gemini-3.1-pro-preview|restricted|lb100_gemini-3.1-pro-preview_seed0.json"
        "haiku45_full_continue|claude-haiku-4-5-20251001|full|lb100_haiku45_oraclefull_seed0.json"
    )
    for spec in "${SPECS[@]}"; do
        IFS='|' read -r short model conds outname <<< "$spec"
        local log="$LOGS/resume_${short}_${TS}.log"
        sleep "$stagger"
        nohup "$PY" -u scripts/run_leaderboard_100_ablation.py \
            --model "$model" --seeds 0 --conditions $conds \
            --output "$RESULTS/$outname" > "$log" 2>&1 &
        echo "  [api] $short PID=$! → $(basename $log)"
        stagger=$((stagger + 5))
    done
}

cmd_api() {
    check_api_env || { red "Aborting — API env not ready"; return 1; }
    check_harness_fixes >/dev/null || { red "Aborting — harness fixes missing"; return 1; }
    bold "=== launching 8 API resumes ==="
    launch_api_jobs
    green "All API jobs launched. Check status: $0 status"
}

cmd_oss() {
    check_oss_env || { red "Aborting — OSS env not ready"; return 1; }
    check_harness_fixes >/dev/null || { red "Aborting — harness fixes missing"; return 1; }
    bold "=== launching OSS sweep (18 models, sequential) ==="
    nohup bash scripts/run_all_opensource_100_ablation.sh > "$LOGS/oss_${TS}.log" 2>&1 &
    echo "  [oss] PID=$!  → $LOGS/oss_${TS}.log"
    green "OSS launcher started. Check status: $0 status"
}

cmd_qwen() {
    check_oss_env || { red "Aborting — OSS env not ready"; return 1; }
    check_harness_fixes >/dev/null || { red "Aborting — harness fixes missing"; return 1; }
    yellow "Qwen-only mode runs the full OSS launcher; non-Qwen models are handled by Option A only."
    yellow "If you need pure Qwen-only sequencing, edit scripts/run_all_opensource_100_ablation.sh and comment out non-Qwen lines."
    bold "=== launching OSS sweep (filter to Qwen if you edited the script) ==="
    nohup bash scripts/run_all_opensource_100_ablation.sh > "$LOGS/oss_qwen_${TS}.log" 2>&1 &
    echo "  PID=$!  → $LOGS/oss_qwen_${TS}.log"
}

cmd_status() {
    python3 scripts/lb100_status.py "$@"
}

cmd_regrade() {
    local ckpt="${1:-}"
    if [ -z "$ckpt" ]; then
        red "usage: $0 regrade <checkpoint.jsonl>"
        return 2
    fi
    python3 scripts/regrade_lb100_checkpoint_safe.py "$ckpt"
}

case "${1:-}" in
    check)   cmd_check ;;
    sync)    shift; cmd_sync "$@" ;;
    api)     cmd_api ;;
    oss)     cmd_oss ;;
    qwen)    cmd_qwen ;;
    status)  shift; cmd_status "$@" ;;
    regrade) shift; cmd_regrade "$@" ;;
    ""|help|-h|--help)
        bold "Usage:"
        sed -n '3,15p' "$0" | sed 's/^# //'
        ;;
    *)
        red "Unknown command: $1"
        exit 2
        ;;
esac
