#!/usr/bin/env bash
# Generate all paper-ready outputs from combined ablation data.
# Usage: bash scripts/generate_paper.sh
set -e

ABLATION_FILES=""
for f in shared/ablation_test.json shared/ablation_5task.json shared/ablation_10task.json; do
    [ -f "$f" ] && ABLATION_FILES="$ABLATION_FILES $f"
done

if [ -z "$ABLATION_FILES" ]; then
    echo "No ablation files found. Run ablation first."
    exit 1
fi

echo "=== Ablation files: $ABLATION_FILES ==="

echo ""
echo "=== Generating LaTeX tables + statistical analysis ==="
python3 -m harness.paper_tables --ablation $ABLATION_FILES --output-dir shared/paper/

echo ""
echo "=== Generating figure data (CSV/JSON) ==="
python3 -m harness.paper_figures --ablation $ABLATION_FILES --output-dir shared/paper/figures/

echo ""
echo "=== Generating matplotlib figures (PDF) ==="
python3 -m harness.plot_results --ablation $ABLATION_FILES --output-dir shared/paper/figures/

echo ""
echo "=== Generating benchmark stats ==="
python3 -m harness.benchmark_stats --json --output shared/benchmark_stats.json
python3 -m harness.benchmark_stats --latex --output shared/paper/table1_distribution.tex

echo ""
echo "=== Computing per-task TNI ==="
# Prefer JSON-based TNI (more reliable) over runs-dir
python3 -m harness.compute_tni --ablation $ABLATION_FILES --output shared/paper/tni_report.json

# Also compute from runs-dir if available (may include incomplete data)
if [ -d "shared/ablation_runs" ]; then
    python3 -m harness.compute_tni --runs-dir shared/ablation_runs --output shared/paper/tni_from_runs.json 2>/dev/null || true
fi

echo ""
echo "=== All paper outputs generated ==="
echo "LaTeX tables:  shared/paper/table*.tex"
echo "Figures:       shared/paper/figures/*.pdf"
echo "Data:          shared/paper/figures/*.csv"
echo "JSON summary:  shared/paper/ablation_summary.json"
echo "Stats:         shared/benchmark_stats.json"
echo "TNI report:    shared/paper/tni_report.json"
