#!/usr/bin/env bash
# Setup for CR4: Install Python dependencies
pip install flask>=2.3.0 pytest>=7.0.0 pytest-flask>=1.2.0 --quiet 2>/dev/null || true
exit 0
