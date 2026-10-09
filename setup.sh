#!/bin/zsh
# One-time setup: create a private Python environment and install PyObjC.
# Ignores any company pip config (e.g. a private Artifactory mirror) and uses public PyPI.
cd "$(dirname "$0")"
export PIP_CONFIG_FILE=/dev/null
python3 -m venv .venv && .venv/bin/pip install -q --index-url https://pypi.org/simple --upgrade pip pyobjc-framework-Cocoa && echo "Setup done."
