#!/usr/bin/env bash
# dev-setup.sh — One-shot setup for new OGX contributors.
#
# What each step does:
#   1. Python version check  — OGX requires exactly Python 3.12. Pre-commit
#      hooks are only tested against 3.12; using another version may cause
#      the hooks to silently pass locally while failing in CI.
#   2. uv sync               — Installs all dependencies (including dev extras)
#      into the project's virtual environment using the locked versions in
#      uv.lock. This ensures every contributor uses identical package versions.
#   3. pre-commit install    — Registers Git hooks so that linting, formatting,
#      and the f-string logging check all run automatically before each commit.
#      Skipping this step means CI may reject your first push.
#
# Usage:
#   bash scripts/dev-setup.sh
#
# After running this script, activate the virtual environment:
#   source .venv/bin/activate

set -euo pipefail

REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=12

# ---------------------------------------------------------------------------
# Step 1: Verify Python version
# ---------------------------------------------------------------------------
echo "[1/3] Checking Python version..."

if ! command -v python3 &>/dev/null; then
    echo "Error: Failed to find python3 on PATH. Install Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR} and try again." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -ne "$REQUIRED_PYTHON_MAJOR" || "$PYTHON_MINOR" -ne "$REQUIRED_PYTHON_MINOR" ]]; then
    echo "Error: Failed Python version check. Found Python ${PYTHON_VERSION}, but OGX requires Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR}." >&2
    echo "Install Python 3.12 (e.g. via pyenv: pyenv install 3.12) and ensure it is active before running this script." >&2
    exit 1
fi

echo "    Python ${PYTHON_VERSION} — OK"

# ---------------------------------------------------------------------------
# Step 2: Sync dependencies with uv
# ---------------------------------------------------------------------------
echo "[2/3] Running uv sync..."

if ! command -v uv &>/dev/null; then
    echo "Error: Failed to find uv on PATH. Install uv from https://docs.astral.sh/uv/getting-started/installation/ and try again." >&2
    exit 1
fi

uv sync
echo "    Dependencies synced — OK"

# ---------------------------------------------------------------------------
# Step 3: Install pre-commit hooks
# ---------------------------------------------------------------------------
echo "[3/3] Installing pre-commit hooks..."

uv run pre-commit install
echo "    Pre-commit hooks installed — OK"

echo ""
echo "Setup complete. Activate the virtual environment with:"
echo "    source .venv/bin/activate"
