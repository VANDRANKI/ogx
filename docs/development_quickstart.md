# Development Quickstart

This guide gets you productive in the OGX codebase quickly.
For full contributor guidelines see [AGENTS.md](../AGENTS.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

## Prerequisites

- Python 3.12 (required — pre-commit hooks only work with 3.12)
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
# Install all development dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

## Running Tests

```bash
# Unit tests (fast, no network)
uv run pytest tests/unit/ -x --tb=short

# Full pre-commit check
uv run pre-commit run --all-files

# Integration tests in replay mode (no API keys needed)
uv run --no-sync ./scripts/integration-tests.sh \
  --stack-config server:ci-tests --setup gpt \
  --suite responses
```

## Code Style Rules

- All function signatures must include type hints.
- Use `from ogx.log import get_logger` for logging — never `logging.getLogger`.
- Use key-value style in log calls: `logger.info("msg", key=value)`, not f-strings.
- Error messages must be prefixed with `"Failed to "`.
- No inline imports; prefer explicit top-level imports.
- Do not use exceptions as control flow.

## Adding a New Provider

1. Create a config class in `src/ogx/providers/remote/<name>/config.py`
   using Pydantic `Field` with `description` parameters.
2. Implement the provider class inheriting the appropriate protocol
   (e.g., `Inference`, `Responses`).
3. Register it in `src/ogx/providers/registry/` with a `RemoteProviderSpec`.
4. Run `uv run ./scripts/distro_codegen.py` to update distribution configs.
5. Add integration tests and record initial responses:
   ```bash
   uv run --no-sync ./scripts/integration-tests.sh \
     --stack-config server:ci-tests --setup <name> \
     --inference-mode record-if-missing \
     --suite responses
   ```

## Commit Convention

OGX uses [Conventional Commits](https://www.conventionalcommits.org/).
All commits must be signed off with `git commit -s`.
Use `git merge main` to update branches — not rebase.

## Before Opening a PR

- [ ] `uv run pre-commit run --all-files` passes
- [ ] New parameters have `description` in their Pydantic `Field`
- [ ] Integration test recordings are committed if request bodies changed
- [ ] `README.md` and relevant module `README.md` files are updated
- [ ] PR description includes a testing script and execution output
