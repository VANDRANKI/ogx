#!/usr/bin/env bash
# Run all quality checks that CI requires, in order.
# Usage: ./scripts/dev-check.sh
set -euo pipefail

echo "==> Running pre-commit hooks on all files..."
uv run pre-commit run --all-files

echo "==> Running unit tests..."
./scripts/unit-tests.sh

echo ""
echo "All checks passed. Your branch is ready for PR."
