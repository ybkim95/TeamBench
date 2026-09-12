#!/usr/bin/env bash
# Wait for all Gemma 4 models to be downloaded, then start evaluation
set -euo pipefail

echo "[$(date)] Waiting for Gemma 4 model downloads to complete..."

check_model() {
    python3 -c "
from huggingface_hub import try_to_load_from_cache
import os
try:
    path = try_to_load_from_cache('$1', 'config.json')
    if path and os.path.exists(path):
        print('ready')
    else:
        print('missing')
except:
    print('missing')
" 2>/dev/null
}

while true; do
    ready=0
    for model in google/gemma-4-31B-it google/gemma-4-26B-A4B-it google/gemma-4-E4B-it google/gemma-4-E2B-it; do
        status=$(check_model "$model")
        if [ "$status" = "ready" ]; then
            ready=$((ready + 1))
        fi
    done
    
    echo "[$(date)] Models ready: $ready/4"
    
    if [ "$ready" -eq 4 ]; then
        echo "[$(date)] All 4 models downloaded. Starting evaluation pipeline..."
        break
    fi
    
    sleep 60
done

# Launch the full evaluation
cd /u/ybkim95/TeamBench
exec bash scripts/run_gemma4_full.sh
