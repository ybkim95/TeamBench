#!/bin/bash
# set -e removed by grader-audit fix
WORKSPACE_DIR="$1"
ATTESTATION_FILE="$2"

# Check if attestation exists
if [ ! -f "$ATTESTATION_FILE" ]; then
    echo "FAIL: Missing attestation.json"
    exit 1
fi

# Run tests
cd "$WORKSPACE_DIR"
python test_calculator.py > test_output.txt 2>&1

if [ $? -eq 0 ]; then
    # Check if the bug was actually fixed
    if grep -q "a \* b" calculator.py; then
        echo "FAIL: Bug not fixed - still using multiplication instead of division"
        exit 1
    fi
    
    if grep -q "a / b" calculator.py; then
        echo "PASS: Bug fixed and tests pass"
        exit 0
    else
        echo "FAIL: Division operation not found in fixed code"
        exit 1
    fi
else
    echo "FAIL: Tests failed"
    cat test_output.txt
    exit 1
fi