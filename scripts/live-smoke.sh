#!/usr/bin/env bash
# Live production smoke for the Python SDK — anonymous signup + inference.
# No secrets required. Safe to run from CI (workflow_dispatch) or locally.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${AINFERA_API_BASE:-https://api.ainfera.ai}"

echo "→ SDK live smoke (API=${API_BASE})"

if ! curl -sf "${API_BASE%/}/health" >/dev/null; then
  echo "✗ API health check failed: ${API_BASE}/health" >&2
  exit 1
fi

cd "$ROOT"

if command -v uv >/dev/null 2>&1; then
  uv sync --quiet
  uv run python examples/quickstart.py
else
  python3 -m pip install --quiet -e .
  python3 examples/quickstart.py
fi

echo "✅ SDK live smoke PASS"
