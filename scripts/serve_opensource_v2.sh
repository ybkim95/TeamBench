#!/bin/bash
# Serve open-source models with correct vLLM tool-calling flags.
#
# Usage:
#   bash scripts/serve_opensource_v2.sh qwen25-coder
#   bash scripts/serve_opensource_v2.sh glm45-air
#   bash scripts/serve_opensource_v2.sh qwen3-coder

set -e

MODEL="${1:?Usage: $0 <qwen25-coder|glm45-air|qwen3-coder>}"

case "$MODEL" in
    qwen25-coder)
        echo "Starting Qwen2.5-Coder-32B-Instruct (hermes parser, BF16)"
        vllm serve Qwen/Qwen2.5-Coder-32B-Instruct \
            --tensor-parallel-size 2 \
            --max-model-len 32768 \
            --enable-auto-tool-choice \
            --tool-call-parser hermes \
            --dtype bfloat16 \
            --port 8000
        ;;
    glm45-air)
        echo "Starting GLM-4.5-Air-FP8 (glm45 parser, MoE)"
        vllm serve zai-org/GLM-4.5-Air-FP8 \
            --tensor-parallel-size 2 \
            --max-model-len 32768 \
            --enable-auto-tool-choice \
            --tool-call-parser glm45 \
            --dtype float8_e4m3fn \
            --port 8000
        ;;
    qwen3-coder)
        echo "Starting Qwen3-Coder-30B-A3B-FP8 (qwen3_coder parser, MoE)"
        vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 \
            --tensor-parallel-size 2 \
            --max-model-len 32768 \
            --enable-auto-tool-choice \
            --tool-call-parser qwen3_coder \
            --dtype float8_e4m3fn \
            --port 8000
        ;;
    llama4-scout)
        echo "Starting Llama-4-Scout-17B-16E-Instruct (llama3_json parser, MoE)"
        vllm serve meta-llama/Llama-4-Scout-17B-16E-Instruct \
            --tensor-parallel-size 2 \
            --max-model-len 32768 \
            --enable-auto-tool-choice \
            --tool-call-parser llama3_json \
            --dtype bfloat16 \
            --port 8000
        ;;
    *)
        echo "Unknown model: $MODEL"
        echo "Available: qwen25-coder, glm45-air, qwen3-coder, llama4-scout"
        exit 1
        ;;
esac
