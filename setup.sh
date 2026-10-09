#!/bin/zsh
# One-time setup: create a private Python environment and install PyObjC.
cd "$(dirname "$0")"
python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip pyobjc-framework-Cocoa && echo "Setup done."
