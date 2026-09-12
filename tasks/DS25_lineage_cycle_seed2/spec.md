# DS25: Data Lineage Cycle Detection

## Task
Find and break all cycles in a ML feature derivation pipeline with **8 nodes**
and **10 edges**. The graph contains **2 deliberate cycles** introduced
by circular dependency errors.

## Goal: Minimum Edge Removal
Remove the **minimum** number of edges to make the graph a DAG (acyclic).
Each cycle requires exactly **one edge removed** (the back edge in DFS order).

## The Bug
The current script removes ALL edges in a found cycle path, not just the back edge.
This destroys valid pipeline dependencies unnecessarily.

**Example**:
- Cycle: A → B → C → A
- Correct: remove ONE back edge (e.g., C→A)
- Buggy: removes A→B, B→C, AND C→A (3 edges)

## Data
File: `data/pipeline_edges.csv`
- `source`: upstream node (feature_N)
- `target`: downstream node (feature_N)

## Requirements
1. Load `data/pipeline_edges.csv`
2. Use DFS to find **back edges** (edges that create cycles)
3. Remove only back edges — minimum one per cycle
4. Verify resulting graph is acyclic
5. Save to `results.json`:
   - `edges_removed`: count of removed edges (should be ~2)
   - `remaining_edges`: count of edges after removal
   - `is_acyclic`: `true`
   - `min_removal_used`: `true`
   - `removed_edges`: list of {source, target} dicts
6. Fix `detect_cycles.py`

## Deliverables
- Fixed `detect_cycles.py`
- `results.json` with minimum removed edges
