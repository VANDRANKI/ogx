# Getting Started with OGX Development

This guide walks you through setting up OGX for local development.

## Prerequisites

- Python 3.12 (required — pre-commit hooks only work with 3.12)
- `uv` for dependency management

## Installation

```bash
# Clone the repository
git clone https://github.com/ogx-project/ogx
cd ogx

# Install dependencies and run
uv run uvicorn ogx.main:app --reload
```

## Running Tests

```bash
# Unit tests
./scripts/unit-tests.sh

# Or directly with pytest
uv run pytest tests/unit/ -x --tb=short

# Integration tests (replay mode — no API keys needed)
uv run --no-sync ./scripts/integration-tests.sh \
  --stack-config server:ci-tests --setup gpt \
  --suite responses
```

## Pre-commit Hooks

Install and run pre-commit checks:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Adding a New Provider

1. Create provider spec in `src/ogx/providers/registry/`
2. Implement the provider class in `src/ogx/providers/remote/` or `src/ogx/providers/inline/`
3. Add configuration class with Pydantic `Field` and `description` parameters
4. Run codegen scripts after config changes:

```bash
uv run ./scripts/distro_codegen.py
uv run ./scripts/provider_codegen.py
```

5. Write integration tests with recordings for replay-mode CI

## Logging

Always use the project logger with key-value style:

```python
from ogx.log import get_logger

logger = get_logger(__name__)
logger.info("Processing request", model=model_id, provider=provider)
```

Never use f-strings or `%`-style formatting in log calls.

## Git Conventions

- Use `--signoff` (`-s`) on all commits: `git commit -s -m "feat: ..."`
- Use `git merge main` to update branches (not rebase)
- Follow [Conventional Commits](https://www.conventionalcommits.org/) format
- Error messages must be prefixed with `"Failed to ..."`
