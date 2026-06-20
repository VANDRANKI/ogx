# Development Environment

Step-by-step setup for OGX contributors.

## Prerequisites

- Python 3.12 (required — pre-commit hooks enforce this)
- `uv` package manager
- Docker (for integration tests that need a running server)

## Initial setup

```bash
git clone https://github.com/your-org/ogx.git
cd ogx

# Install all dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Verify the setup
uv run pytest tests/unit/ -x --tb=short
```

## Running the server locally

```bash
# Start with the CI test distribution (no real API keys needed)
uv run python -m ogx.server --stack-config server:ci-tests
```

## Pre-commit hooks summary

| Hook | What it checks |
|------|---------------|
| `Block f-string logging` | All log calls use key-value style, not f-strings |
| `Ensure 'ogx.log' usage` | Logging uses project logger, not `logging.getLogger` |
| `Check API spec for breaking changes` | OpenAPI spec does not regress |
| `mypy` | Type annotations are valid |

If a hook blocks your commit, fix the reported issue — do not bypass with
`--no-verify`.

## Updating generated files

After modifying provider configs, always regenerate:

```bash
uv run ./scripts/distro_codegen.py
uv run ./scripts/provider_codegen.py
uv run ./scripts/run_openapi_generator.sh
```

Commit the generated changes alongside your source changes.
