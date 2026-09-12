#!/usr/bin/env python3
"""Wire the run-scoped TurnBudget through every AgentLoop construction.

Before: each role got its own `max_turns`, so ablation conditions ran at 20 to 140
LLM turns depending on how many phases they had. Solo-vs-Team differences were
confounded with a 7x compute gap (see harness/agent_loop.py::TurnBudget).

After: `run_ablation_condition` and the orchestrators build one TurnBudget per run
and hand it to every AgentLoop, so all conditions spend from the same pool.

The edit is done on the AST so it cannot corrupt formatting, and it is idempotent:
an AgentLoop call that already passes `budget=` is left alone.
"""
import ast
import sys

TARGETS = {
    "harness/ablation.py": "budget",
    "harness/orchestrator.py": "self.budget",
}


def wire(path: str, expr: str) -> tuple[int, int]:
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    edits = []  # (lineno, col_offset of the closing paren) for calls needing budget
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
        if name != "AgentLoop":
            continue
        total += 1
        if any(kw.arg == "budget" for kw in node.keywords):
            continue
        edits.append(node)

    if not edits:
        return 0, total

    lines = src.splitlines(keepends=True)
    # Offset of the end of each call, as an absolute character index.
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln))

    def abs_pos(lineno: int, col: int) -> int:
        return starts[lineno - 1] + col

    # Insert immediately after the LAST argument expression rather than before the
    # closing paren. A trailing `# comment` sits between the last argument and the
    # paren, and inserting after it lands the new keyword inside the comment.
    points = []
    for n in edits:
        args = list(n.args) + [kw.value for kw in n.keywords]
        if args:
            last = max(args, key=lambda a: (a.end_lineno, a.end_col_offset))
            points.append(abs_pos(last.end_lineno, last.end_col_offset))
        else:
            points.append(abs_pos(n.end_lineno, n.end_col_offset) - 1)
    for p in sorted(points, reverse=True):
        src = src[:p] + f", budget={expr}" + src[p:]

    ast.parse(src)  # fail loudly rather than write a broken file
    open(path, "w", encoding="utf-8").write(src)
    return len(edits), total


if __name__ == "__main__":
    rc = 0
    for path, expr in TARGETS.items():
        try:
            added, total = wire(path, expr)
            print(f"{path}: wired {added} of {total} AgentLoop constructions "
                  f"({total - added} already had one)")
        except SyntaxError as e:
            print(f"{path}: REFUSED, edit would break the file: {e}", file=sys.stderr)
            rc = 1
    sys.exit(rc)
