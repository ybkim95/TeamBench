#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/data/input" "$WORKSPACE/data/output" "$REPORTS"

cat > "$WORKSPACE/data/input/records.csv" <<'CSV'
id,name,score,department
1,Alice,85,engineering
2,Bob,92,sales
3,Charlie,78,
4,Diana,N/A,marketing
5,Eve,105,engineering
2,Bob,88,sales
6,Frank,45,
7,Grace,92,engineering
1,Alice,90,engineering
8,Heidi,-5,sales
CSV
