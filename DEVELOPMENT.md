# OGX Development Guide

Practical notes for contributors. See `AGENTS.md` for agent-specific
guidelines and `CONTRIBUTING.md` for the full contribution process.

## Requirements

- **Python 3.12** (enforced by pre-commit hooks)
- `uv` for dependency management

## Setup

```bash
git clone https://github.com/VANDRANKI/ogx.git
cd ogx
uv sync
```

## Running the Server Locally

```bash
# Default distribution
uv run python -m ogx --stack-config server:ci-tests
```

## Unit Tests

```bash
uv run pytest tests/unit/ -x --tb=short
# or via the convenience wrapper:
./scripts/unit-tests.sh
```

## Integration Tests (Replay Mode — no API keys)

```bash
uv run --no-sync ./scripts/integration-tests.sh \
  --stack-config server:ci-tests --setup gpt \
  --suite responses
```

If a test fails with "Recording not found", re-run with
`--inference-mode record-if-missing` (requires `OPENAI_API_KEY`).

## Pre-commit Hooks

Install once:
```bash
uv run pre-commit install
```

Run manually across all files:
```bash
uv run pre-commit run --all-files
```

Key hooks to be aware of:
- **Block f-string logging** — use `logger.info("msg", key=value)` not f-strings
- **Check API spec for breaking changes** — regenerate with `./scripts/run_openapi_generator.sh`

## Structured Logging

```python
# Always use ogx.log
from ogx.log import get_logger
logger = get_logger(__name__)

# Key-value style — the pre-commit hook enforces this
logger.info("Processing request", model=model_id, provider=provider)

# NOT this:
logger.info(f"Processing request for {model_id}")  # blocked by hook
```

## Error Messages

All error messages must start with `"Failed to ..."` — this is checked
in code review.

## Commit Style

Use Conventional Commits with `--signoff`:

```bash
git commit -s -m "feat(responses): add stream-level tool call support"
```

Do **not** amend commits during PR review — use new commits instead.
