"""
Cycle detection and removal for data warehouse pipeline dependency graph.
BUG: Detects cycles via DFS but removes ALL edges in the found cycle path,
not just the minimum (one back edge per cycle). This over-removes edges,
breaking valid dependencies.

Fix: Use DFS to find back edges specifically (edges that point to an ancestor
in the DFS tree). Remove only back edges — one per cycle is sufficient.
"""
import pandas as pd
import json

df = pd.read_csv("data/pipeline_edges.csv")

# Build adjacency list
graph = {}
for _, row in df.iterrows():
    graph.setdefault(row["source"], []).append(row["target"])
    graph.setdefault(row["target"], [])

nodes = list(graph.keys())

def find_cycle_dfs(graph):
    """Returns a cycle as a list of nodes, or None if no cycle."""
    visited = set()
    rec_stack = []

    def dfs(node):
        visited.add(node)
        rec_stack.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                result = dfs(neighbor)
                if result is not None:
                    return result
            elif neighbor in rec_stack:
                # Found cycle
                idx = rec_stack.index(neighbor)
                return rec_stack[idx:]
        rec_stack.pop()
        return None

    for node in nodes:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None

edges_to_remove = []
removed_set = set()
max_iter = 20

for _ in range(max_iter):
    cycle = find_cycle_dfs(graph)
    if not cycle:
        break
    # BUG: removes ALL edges in the cycle, not just the back edge
    for i in range(len(cycle)):
        src = cycle[i]
        dst = cycle[(i + 1) % len(cycle)]
        if dst in graph.get(src, []) and (src, dst) not in removed_set:
            graph[src].remove(dst)
            edges_to_remove.append({"source": src, "target": dst})
            removed_set.add((src, dst))
            # BUG: should break here after removing one edge per cycle

remaining_edges = [
    {"source": s, "target": t}
    for s, neighbors in graph.items()
    for t in neighbors
]

results = {
    "edges_removed": len(edges_to_remove),
    "remaining_edges": len(remaining_edges),
    "is_acyclic": True,
    "min_removal_used": False,  # BUG: should be True
    "removed_edges": edges_to_remove,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Removed {len(edges_to_remove)} edges (may be more than minimum!)")
