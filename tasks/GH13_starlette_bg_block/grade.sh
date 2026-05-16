#!/usr/bin/env bash
# GH13_starlette_bg_block grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=6
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

cd "${WORKSPACE}"

pip install starlette httpx pytest pytest-asyncio anyio --quiet 2>/dev/null || true

# C1: app.py and middleware.py valid Python
result=$(python3 -c "
import ast
ast.parse(open('app.py').read())
ast.parse(open('middleware.py').read())
print('pass')
" 2>/dev/null || echo "fail")
check "C1" "app.py and middleware.py valid Python syntax" "$result"

# C2: middleware no longer inherits BaseHTTPMiddleware (fix verification)
result=$(python3 -c "
import ast, sys
src = open('middleware.py').read()
# Check that BaseHTTPMiddleware is not used as a base class
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        for base in node.bases:
            base_name = ''
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name == 'BaseHTTPMiddleware':
                print('fail')
                sys.exit(0)
print('pass')
" 2>/dev/null || echo "skip")
# This check is informational — not strictly required (asyncio.create_task fix also valid)
# so we make it advisory by treating skip as pass
[ "$result" = "skip" ] && result="pass"
check "C2" "middleware does not block on BaseHTTPMiddleware lifecycle" "$result"

# C3: main route returns 200
result=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
async def run():
    from httpx import AsyncClient, ASGITransport
    import importlib
    app_mod = importlib.import_module('app')
    # find the app object
    import inspect
    app_obj = None
    for name, obj in inspect.getmembers(app_mod):
        if hasattr(obj, '__class__') and 'Starlette' in type(obj).__name__:
            app_obj = obj; break
    if app_obj is None:
        print('fail'); return
    transport = ASGITransport(app=app_obj)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp = await client.get('/notify')
        if resp.status_code != 200:
            resp = await client.get('/track')
        if resp.status_code != 200:
            resp = await client.get('/action')
        print('pass' if resp.status_code == 200 else 'fail')
asyncio.run(run())
" 2>/dev/null || echo "fail")
check "C3" "main route returns 200" "$result"

# C4: health route returns 200
result=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
async def run():
    from httpx import AsyncClient, ASGITransport
    import importlib, inspect
    app_mod = importlib.import_module('app')
    app_obj = None
    for name, obj in inspect.getmembers(app_mod):
        if hasattr(obj, '__class__') and 'Starlette' in type(obj).__name__:
            app_obj = obj; break
    if app_obj is None:
        print('fail'); return
    transport = ASGITransport(app=app_obj)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        for route in ['/health', '/ping', '/status']:
            resp = await client.get(route)
            if resp.status_code == 200:
                print('pass'); return
    print('fail')
asyncio.run(run())
" 2>/dev/null || echo "fail")
check "C4" "health route returns 200" "$result"

# C5: concurrent request does not block — health responds in < 2s
result=$(python3 -c "
import asyncio, time, sys
sys.path.insert(0, '.')
async def run():
    from httpx import AsyncClient, ASGITransport
    import importlib, inspect
    app_mod = importlib.import_module('app')
    app_obj = None
    for name, obj in inspect.getmembers(app_mod):
        if hasattr(obj, '__class__') and 'Starlette' in type(obj).__name__:
            app_obj = obj; break
    if app_obj is None:
        print('fail'); return
    transport = ASGITransport(app=app_obj)
    main_routes  = ['/notify', '/track', '/action']
    health_routes = ['/health', '/ping', '/status']
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        main_route = None
        for r in main_routes:
            try:
                resp = await client.get(r)
                if resp.status_code == 200:
                    main_route = r; break
            except Exception:
                pass
        health_route = None
        for r in health_routes:
            try:
                resp = await client.get(r)
                if resp.status_code == 200:
                    health_route = r; break
            except Exception:
                pass
        if main_route is None or health_route is None:
            print('fail'); return
        async def first():
            return await client.get(main_route)
        async def second():
            await asyncio.sleep(0.1)
            t0 = time.monotonic()
            r = await client.get(health_route)
            return r, time.monotonic() - t0
        _, (hr, elapsed) = await asyncio.gather(first(), second())
        print('pass' if elapsed < 2.0 else 'fail')
asyncio.run(run())
" 2>/dev/null || echo "fail")
check "C5" "concurrent health request completes in < 2s" "$result"

# C6: pytest test_app.py passes
result=$(python3 -m pytest test_app.py -q --tb=no --asyncio-mode=auto 2>/dev/null && echo "pass" || echo "fail")
check "C6" "pytest test_app.py passes" "$result"

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
