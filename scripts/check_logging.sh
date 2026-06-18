#!/usr/bin/env bash
# Detect f-string and %-style logging calls that violate the OGX logging policy.
# Run this before committing to catch violations before the pre-commit hook.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src"

echo "Checking for f-string logging violations in $SRC..."

# Match logger.{level}(f"...")
F_STRING_VIOLATIONS=$(grep -rn --include='*.py' \
  'logger\.(debug|info|warning|error|critical)(f"' "$SRC" 2>/dev/null || true)

# Match logger.{level}("...", var) using %-style embedded %s in the string
PCT_VIOLATIONS=$(grep -rn --include='*.py' \
  'logger\.(debug|info|warning|error|critical)("[^"]*%[sd' "$SRC" 2>/dev/null || true)

found=0

if [[ -n "$F_STRING_VIOLATIONS" ]]; then
  echo
  echo "F-STRING LOGGING VIOLATIONS (use keyword args instead):"
  echo "$F_STRING_VIOLATIONS"
  found=1
fi

if [[ -n "$PCT_VIOLATIONS" ]]; then
  echo
  echo "%-STYLE LOGGING VIOLATIONS (use keyword args instead):"
  echo "$PCT_VIOLATIONS"
  found=1
fi

if [[ $found -eq 0 ]]; then
  echo "No logging violations found. OK."
else
  echo
  echo "Fix: replace logger.info(f\"msg {var}\") with logger.info(\"msg\", var=var)"
  exit 1
fi
