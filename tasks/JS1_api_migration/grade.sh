#!/usr/bin/env bash
set -euo pipefail
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

# ── 1. package.json pins express >= 5 ─────────────────────────────────────────
check "node -e \"
const pkg = require('./package.json');
const dep = pkg.dependencies && pkg.dependencies.express || '';
// Accept ^5, ~5, 5.x, >=5, 5.0.0, etc.
const match = dep.match(/[\^~>=]*(\d+)/);
if (!match) throw new Error('no express dep');
const major = parseInt(match[1], 10);
if (major < 5) throw new Error('express major < 5: ' + dep);
console.log('EXPRESS_VERSION_OK');
\"" "express_not_v5"

# ── 2. No req.param( calls remain (ignore comment lines) ──────────────────────
check "! grep -v '^\s*//' server.js | grep -q 'req\.param('" "req_param_not_removed"

# ── 3. No app.del( calls remain (ignore comment lines) ────────────────────────
check "! grep -v '^\s*//' server.js | grep -q 'app\.del('" "app_del_not_renamed"

# ── 4. No two-arg res.json( pattern remains ───────────────────────────────────
# Match res.json(anything, number) — a trailing status integer as 2nd arg
check "! node -e \"
const fs = require('fs');
const src = fs.readFileSync('server.js', 'utf8');
// Match res.json(<expr>, <digits>) — crude but reliable for this codebase
if (/res\.json\([^)]+,\s*\d+\s*\)/.test(src)) {
  throw new Error('old res.json(data, status) pattern found');
}
console.log('RES_JSON_OK');
\"" "res_json_old_signature"

# ── 5. Server starts without error ────────────────────────────────────────────
check "
  # Install deps if node_modules absent
  if [ ! -d node_modules ]; then
    npm install --prefer-offline --silent 2>/dev/null || npm install --silent 2>/dev/null
  fi
  # Start server, wait up to 6 s for it to bind
  node server.js &
  SERVER_PID=\$!
  trap 'kill \$SERVER_PID 2>/dev/null || true' EXIT
  for i in \$(seq 1 20); do
    sleep 0.3
    if node -e \"
      const http = require('http');
      http.get('http://localhost:3000/tasks', (r) => {
        process.exit(r.statusCode === 200 ? 0 : 1);
      }).on('error', () => process.exit(1));
    \" 2>/dev/null; then
      echo 'SERVER_START_OK'
      break
    fi
  done
  kill \$SERVER_PID 2>/dev/null || true
" "server_start_failed"

# ── 6. All 5 tests pass ───────────────────────────────────────────────────────
check "
  if [ ! -d node_modules ]; then
    npm install --prefer-offline --silent 2>/dev/null || npm install --silent 2>/dev/null
  fi
  node test/api.test.js
" "tests_failed"

# ── 7. attestation.json verdict=pass ─────────────────────────────────────────
check "node -e \"
const att = JSON.parse(require('fs').readFileSync('$SUBMISSION/attestation.json', 'utf8'));
if (att.verdict !== 'pass') throw new Error('verdict is ' + att.verdict);
console.log('ATTESTATION_OK');
\"" "bad_attestation"

# ── Score ─────────────────────────────────────────────────────────────────────
PARTIAL=$(node -e "console.log(Math.round($PASSED / Math.max(1, $CHECKS) * 100) / 100)")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(node -e "
const f = '${FAILURES}';
const arr = f.split(',').filter(Boolean);
console.log(JSON.stringify(arr));
")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
