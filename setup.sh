#!/bin/zsh
# One-time setup: create a private Python environment and install PyObjC.
# Ignores any company pip config (e.g. a private Artifactory mirror) and uses public PyPI.
cd "$(dirname "$0")"
export PIP_CONFIG_FILE=/dev/null PIP_INDEX_URL=https://pypi.org/simple
rm -rf .venv
python3 -m venv .venv \
  && .venv/bin/pip install -q --upgrade pip \
  && .venv/bin/pip install -q --only-binary=:all: -r requirements.txt \
  && echo "Setup done."
