#!/usr/bin/env bash
# setup.sh for INC5_cert_expiry
# Generates seed-specific workspace files using the parameterized generator.
#
# Args: $1=WORKSPACE $2=REPORTS $3=RUN_ID [optional: $4=SEED]
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="${3:-0}"
SEED="${4:-0}"

mkdir -p "$WORKSPACE" "$REPORTS"

# Generate seed-specific files via the Python generator
python3 - <<PYEOF
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('$WORKSPACE'))))
from generators.gen_inc5_cert_expiry import Generator

gen = Generator()
task = gen.generate(int("$SEED"))

import json, os

# Write workspace files
for rel_path, content in task.workspace_files.items():
    abs_path = os.path.join("$WORKSPACE", rel_path)
    parent = os.path.dirname(abs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

# Write expected.json to reports (grader only — never seen by agents)
with open(os.path.join("$REPORTS", "expected.json"), "w", encoding="utf-8") as f:
    json.dump(task.expected, f, indent=2)

print(f"INC5_cert_expiry seed=$SEED setup complete: {len(task.workspace_files)} workspace files written.")
PYEOF
