# DS23: Fuzzy Dedup with Transitive Closure

## Task
Deduplicate 19 product records using fuzzy string matching
(Levenshtein edit distance ≤ 3) with **transitive closure** clustering.

## The Transitive Closure Problem
Naive pairwise matching misses transitive duplicates:
- Record A: "Acme Corp"
- Record B: "Acme Corp."  (dist=1, matches A)
- Record C: "Acme Corp. Inc"  (dist=5 from A — no direct match, but matches B with dist=4)

Without transitive closure: 2 clusters {A,B} and {C}
With transitive closure: 1 cluster {A,B,C}

## Data
File: `data/records.csv`
- `product_id`: unique record identifier
- `product_name`: name string (may contain typos, abbreviations, suffixes)

## Requirements
1. Load `data/records.csv`
2. Compute all pairs with edit_distance(product_name_i, product_name_j) ≤ 3
3. Apply **union-find** (disjoint set union) for transitive closure
4. Assign each record a `cluster_id` (canonical cluster representative)
5. Save to `results.json`:
   - `n_records`: total records
   - `n_pairs`: number of matching pairs found
   - `n_clusters`: number of distinct clusters (should be ~6)
   - `transitive_closure_applied`: `true`
   - `threshold`: 3
   - `clusters`: dict mapping cluster_id -> list of product_ids
6. Fix `dedup.py`

## Deliverables
- Fixed `dedup.py` with union-find transitive closure
- `results.json` with correct cluster assignments
