#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

cd "$WORKSPACE"

EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

# 1. clusters.json exists
check "test -f clusters.json" "clusters_json_missing"

# 2. clusters.json is valid JSON
check "python3 -c \"import json; json.load(open('clusters.json'))\"" "clusters_json_invalid"

# 3. All documents are assigned
check "python3 -c \"
import json, os
clusters = json.load(open('clusters.json'))
docs = [f[:-4] for f in os.listdir('documents') if f.endswith('.txt')]
for d in docs:
    assert d in clusters, f'Missing doc: {d}'
print(f'ALL_ASSIGNED: {len(docs)} docs')
\"" "not_all_docs_assigned"

# 4. Exactly 4 distinct cluster IDs
check "python3 -c \"
import json
clusters = json.load(open('clusters.json'))
ids = set(clusters.values())
assert len(ids) == 4, f'Expected 4 clusters, got {len(ids)}: {ids}'
assert ids == {0,1,2,3}, f'Cluster IDs must be 0-3, got {ids}'
print('FOUR_CLUSTERS')
\"" "wrong_cluster_count"

# 5. No cluster is empty
check "python3 -c \"
import json
from collections import Counter
clusters = json.load(open('clusters.json'))
counts = Counter(clusters.values())
for cid in range(4):
    assert counts.get(cid, 0) > 0, f'Cluster {cid} is empty'
print('NO_EMPTY')
\"" "empty_cluster"

# 6. No cluster has > 60% of documents
check "python3 -c \"
import json
from collections import Counter
clusters = json.load(open('clusters.json'))
counts = Counter(clusters.values())
total = len(clusters)
for cid, cnt in counts.items():
    pct = cnt / total * 100
    assert pct <= 60, f'Cluster {cid} has {pct:.0f}% of docs (max 60%)'
print('SIZE_OK')
\"" "cluster_too_large"

# 7. Pre-labelled documents in correct clusters
check "python3 -c \"
import json
clusters = json.load(open('clusters.json'))
hints = json.load(open('category_hints.json'))
for doc_id, expected_cid in hints.items():
    actual = clusters.get(doc_id)
    assert actual == expected_cid, f'{doc_id}: expected cluster {expected_cid}, got {actual}'
print('HINTS_OK')
\"" "prelabelled_wrong_cluster"

# 8. Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
