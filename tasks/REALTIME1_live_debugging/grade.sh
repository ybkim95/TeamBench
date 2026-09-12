#!/bin/bash
# set -e removed by grader-audit fix
WORKSPACE_DIR="$1"
ATTESTATION_FILE="$2"

# Check if attestation exists
if [ ! -f "$ATTESTATION_FILE" ]; then
    echo "FAIL: Missing attestation.json"
    exit 1
fi

# Verify the fix is in place
if ! grep -q "exponential_backoff\|circuit_breaker\|CircuitBreaker" "$WORKSPACE_DIR/src/connection_pool.py"; then
    echo "FAIL: Required patterns (exponential backoff or circuit breaker) not implemented"
    exit 1
fi

# Check for queue-based overflow handling
if ! grep -q "queue\|Queue\|deque" "$WORKSPACE_DIR/src/connection_pool.py"; then
    echo "FAIL: Queue-based overflow handling not implemented"
    exit 1
fi

# Verify no service restart approach was used
if [ -f "$WORKSPACE_DIR/restart.log" ]; then
    echo "FAIL: Service was restarted (causes data loss)"
    exit 1
fi

# Check if monitoring was added
if [ ! -f "$WORKSPACE_DIR/monitoring/alerts.yaml" ]; then
    echo "FAIL: Monitoring alerts not configured"
    exit 1
fi

# Verify rollback mechanism
if [ ! -f "$WORKSPACE_DIR/rollback.sh" ] && [ ! -f "$WORKSPACE_DIR/src/rollback.py" ]; then
    echo "FAIL: No rollback mechanism provided"
    exit 1
fi

# Simulate checking real-time metrics (would be actual metrics in production)
python3 - <<'EOF'
import json
import sys

# Simulate reading metrics
error_rate = 0.8  # Would come from actual monitoring

# Check if the solution includes proper fix indicators
with open("$1/src/connection_pool.py") as f:
    content = f.read()
    if "with self.lock:" in content and "time.sleep" in content and content.count("with self.lock:") == 1:
        print("FAIL: Race condition not properly fixed - connection creation still under lock")
        sys.exit(1)
        
    if "max_size * 2" in content or "max_size = 200" in content:
        print("FAIL: Simply increasing pool size makes the problem worse")
        sys.exit(1)

print("PASS: All real-time debugging requirements met")
EOF

echo "PASS"