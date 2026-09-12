# DS23: Fuzzy Dedup with Transitive Closure

## Task
Deduplicate 26 company records using fuzzy string matching
(Levenshtein edit distance ≤ 4) with **transitive closure** clustering.

## The Transitive Closure Problem
Naive pairwise matching misses transitive duplicates:
- Record A: "Acme Corp"
- Record B: "Acme Corp."  (dist=1, matches A)
- Record C: "Acme Corp. Inc"  (dist=5 from A — no direct match, but matches B with dist=4)

Without transitive closure: 2 clusters {A,B} and {C}
With transitive closure: 1 cluster {A,B,C}

## Data
File: `data/records.csv`
- `company_id`: unique record identifier
- `company_name`: name string (may contain typos, abbreviations, suffixes)

## Requirements
1. Load `data/records.csv`
2. Compute all pairs with edit_distance(company_name_i, company_name_j) ≤ 4
3. Apply **union-find** (disjoint set union) for transitive closure
4. Assign each record a `cluster_id` (canonical cluster representative)
5. Save to `results.json`:
   - `n_records`: total records
   - `n_pairs`: number of matching pairs found
   - `n_clusters`: number of distinct clusters (should be ~9)
   - `transitive_closure_applied`: `true`
   - `threshold`: 4
   - `clusters`: dict mapping cluster_id -> list of company_ids
6. Fix `dedup.py`

## Deliverables
- Fixed `dedup.py` with union-find transitive closure
- `results.json` with correct cluster assignments
