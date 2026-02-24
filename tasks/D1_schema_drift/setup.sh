#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/data/input" "$WORKSPACE/data/output" "$REPORTS"

cat > "$WORKSPACE/data/input/batch_001.csv" <<'CSV'
id,name,value
1,Alice,100
2,Bob,200
3,Charlie,300
4,Diana,400
5,Eve,150
CSV

cat > "$WORKSPACE/data/input/batch_002.csv" <<'CSV'
id,name,value,category
6,Frank,600,sales
7,Grace,700,engineering
8,Heidi,250,marketing
9,Ivan,500,sales
10,Judy,350,engineering
CSV

cat > "$WORKSPACE/data/input/batch_003.csv" <<'CSV'
id,full_name,value,category
11,Karl,450,marketing
12,Liam,800,sales
13,Mia,320,engineering
14,Noah,670,marketing
15,Olivia,290,sales
CSV

cat > "$WORKSPACE/data/input/batch_004.csv" <<'CSV'
record_id,name,amount,category,region
16,Peter,550,engineering,west
17,Quinn,430,sales,east
18,Rose,710,marketing,west
3,Charlie,350,sales,east
19,Sam,480,engineering,north
CSV

cat > "$WORKSPACE/data/input/batch_005.csv" <<'CSV'
id,name,value,category,_timestamp
20,Tara,600,sales,2025-01-15
3,Charlie,280,engineering,2025-01-16
21,Uma,abc,marketing,2025-01-17
22,Vera,-50,sales,2025-01-18
23,Will,390,engineering,2025-01-19
CSV
