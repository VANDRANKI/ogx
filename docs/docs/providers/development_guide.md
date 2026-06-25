# Provider Development Guide

This guide walks through adding a new remote inference provider to OGX.

## Overview

Providers in OGX implement one or more protocols (e.g. `Inference`, `Responses`)
and are registered via spec files. The architecture separates:

- **Spec** — metadata, config class path, dependencies
- **Config class** — Pydantic model with provider-specific settings
- **Implementation** — the actual API adapter code

## Step 1: Create the Provider Spec

Create a spec file in `src/ogx/providers/registry/remote/`:

```python
# src/ogx/providers/registry/remote/my_provider.py
from ogx.providers.registry.remote_provider_spec import RemoteProviderSpec
from ogx_api.inference import Inference

my_provider_spec = RemoteProviderSpec(
    provider_type="remote::my_provider",
    module="ogx.providers.remote.inference.my_provider",
    config_class="ogx.providers.remote.inference.my_provider.MyProviderConfig",
    api_dependencies=[Inference],
)
```

## Step 2: Define the Config Class

```python
# src/ogx/providers/remote/inference/my_provider.py
from pydantic import Field
from ogx.providers.remote.inference._base import BaseInferenceProviderConfig


class MyProviderConfig(BaseInferenceProviderConfig):
    """Configuration for My Provider inference backend."""

    api_key: str = Field(
        description="API key for authentication. Set via MY_PROVIDER_API_KEY env var."
    )
    base_url: str = Field(
        default="https://api.myprovider.com/v1",
        description="Base URL for the My Provider API endpoint.",
    )
    model: str = Field(
        default="my-model-v1",
        description="Default model identifier to use for inference.",
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds.",
    )
```

**Important:** Every `Field` must have a `description` — this auto-generates docs.

## Step 3: Implement the Provider

```python
from ogx.log import get_logger
from ogx.providers.utils.inference.openai_mixin import OpenAICompatMixin

logger = get_logger(__name__)


class MyProviderInferenceAdapter(OpenAICompatMixin):
    """Inference adapter for My Provider (OpenAI-compatible API)."""

    def __init__(self, config: MyProviderConfig) -> None:
        super().__init__(config)
        logger.info("Initialized My Provider adapter", base_url=config.base_url)
```

If your provider is OpenAI-compatible, `OpenAICompatMixin` handles most of the
work. For custom APIs, implement the `Inference` protocol methods directly.

## Step 4: Register the Spec

Add your spec to the registry index:

```python
# src/ogx/providers/registry/remote/__init__.py
from .my_provider import my_provider_spec

all_remote_specs = [
    # ... existing specs ...
    my_provider_spec,
]
```

## Step 5: Add Integration Tests

```bash
# Record test responses (requires API key)
export MY_PROVIDER_API_KEY=your_key
uv run --no-sync ./scripts/integration-tests.sh \
  --stack-config server:ci-tests \
  --setup my_provider \
  --inference-mode record \
  --file tests/integration/inference/test_my_provider.py

# Commit the recordings
git add tests/integration/*/recordings/
git commit -m "test: add My Provider integration test recordings"
```

## Step 6: Regenerate Docs

```bash
uv run ./scripts/provider_codegen.py
uv run ./scripts/distro_codegen.py
```

## Error Message Convention

All error messages must start with `"Failed to "`:

```python
raise ValueError(f"Failed to authenticate with My Provider: {status_code}")
```

## Logging Convention

Use structured key-value logging:

```python
# Correct
logger.info("Processing request", model=model_id, provider="my_provider")

# Wrong — will fail pre-commit hook
logger.info(f"Processing request for {model_id}")
```
