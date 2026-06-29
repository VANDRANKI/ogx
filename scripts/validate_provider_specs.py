#!/usr/bin/env python3
"""Validate provider registration specs for required fields.

Loads Python modules under src/ogx/providers/registry/, inspects
any dict or object named *_spec or *Spec, and reports missing
required fields before they become runtime errors.

Usage:
    uv run python scripts/validate_provider_specs.py
    uv run python scripts/validate_provider_specs.py --verbose
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

REGISTRY_DIR = Path("src/ogx/providers/registry")

# Fields that every provider spec is expected to declare.
REQUIRED_FIELDS = {"provider_type", "module", "config_class"}


def load_module_from_path(path: Path):
    """Dynamically load a Python module from an absolute file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        return None
    return module


def extract_specs(module) -> list[dict]:
    """Return all spec-like objects (dicts with provider_type) from a module."""
    specs = []
    for name in dir(module):
        obj = getattr(module, name, None)
        if isinstance(obj, dict) and "provider_type" in obj:
            specs.append({"name": name, **obj})
        elif hasattr(obj, "provider_type") and hasattr(obj, "module"):
            # Pydantic/dataclass style spec object
            specs.append(
                {
                    "name": name,
                    **{f: getattr(obj, f, None) for f in REQUIRED_FIELDS},
                }
            )
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    if not REGISTRY_DIR.exists():
        print(f"ERROR: {REGISTRY_DIR} does not exist.", file=sys.stderr)
        return 1

    total_specs = 0
    total_errors = 0

    for py_file in sorted(REGISTRY_DIR.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module = load_module_from_path(py_file)
        if module is None:
            print(f"WARN  Could not load {py_file.relative_to(Path.cwd())}")
            continue

        specs = extract_specs(module)
        for spec in specs:
            total_specs += 1
            missing = [f for f in REQUIRED_FIELDS if not spec.get(f)]
            if missing:
                total_errors += 1
                print(
                    f"FAIL  {py_file.name}::{spec['name']} "
                    f"missing: {', '.join(missing)}"
                )
            elif args.verbose:
                print(f"OK    {py_file.name}::{spec['name']} ({spec['provider_type']})")

    print(f"\nChecked {total_specs} specs — {total_errors} error(s) found.")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
