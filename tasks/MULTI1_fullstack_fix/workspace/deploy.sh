#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP=application.py
export FLASK_ENV=production

echo "Deploying note-taking app..."
echo "FLASK_APP=${FLASK_APP}"
echo "FLASK_ENV=${FLASK_ENV}"

flask run --host=0.0.0.0 --port=5000
