"""Launch vLLM with Gemma 4 support by registering gemma4 config at runtime."""
import sys, os

# Block user-site contamination
for p in list(sys.path):
    if '.local/lib/python3.10/site-packages' in p:
        sys.path.remove(p)

# Register gemma4 as gemma3 variant before vLLM loads
import transformers
from transformers import AutoConfig, Gemma3Config

class Gemma4Config(Gemma3Config):
    model_type = "gemma4"

AutoConfig.register("gemma4", Gemma4Config)
print(f"[gemma4-patch] Registered gemma4 config (transformers {transformers.__version__})")

# Now launch vLLM
sys.argv = [
    "vllm", "serve",
    sys.argv[1] if len(sys.argv) > 1 else "google/gemma-4-12B-it",
    "--tensor-parallel-size", sys.argv[2] if len(sys.argv) > 2 else "1",
    "--port", "8000",
    "--max-model-len", "16384",
    "--gpu-memory-utilization", "0.85",
    "--enforce-eager",
    "--enable-auto-tool-choice",
    "--tool-call-parser", "hermes",
    "--trust-remote-code",
]

from vllm.scripts import main
main()
