# Provider Type Annotation Guide

This guide documents the typing conventions used throughout OGX provider
implementations and explains how to annotate new providers correctly.

## Core Principles

OGX providers must satisfy `mypy` in strict mode. Every public function signature
must have full type annotations. Use Pydantic `Field` with `description` on every
config class attribute — descriptions are used to auto-generate provider docs.

## Config Class Pattern

```python
from typing import Optional
from pydantic import Field
from ogx.providers.remote.inference.config import RemoteInferenceImplConfig


class MyProviderConfig(RemoteInferenceImplConfig):
    """Configuration for the MyProvider remote inference backend."""

    api_key: Optional[str] = Field(
        default=None,
        description=(
            "API key for MyProvider. "
            "If not set, falls back to the MY_PROVIDER_API_KEY environment variable."
        ),
    )
    api_base: str = Field(
        default="https://api.myprovider.com/v1",
        description="Base URL for the MyProvider REST API.",
    )
    model_id: str = Field(
        default="my-model-v1",
        description="MyProvider model identifier to route requests to.",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=600,
        description="Request timeout in seconds. Must be between 1 and 600.",
    )
```

## Inference Protocol Implementation

```python
from typing import AsyncGenerator
from ogx_api.datamodels.inference.chat_completion import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
)
from ogx.providers.utils.inference.openai_mixin import OpenAICompatMixin


class MyProviderInference(OpenAICompatMixin):
    """Inference provider backed by MyProvider."""

    def __init__(self, config: MyProviderConfig) -> None:
        self.config = config

    async def chat_completion(
        self,
        model_id: str,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """Send a non-streaming chat completion request.

        Args:
            model_id: The model identifier to route this request to.
            request: The structured chat completion request.

        Returns:
            A completed ChatCompletionResponse with all candidates populated.

        Raises:
            ProviderError: If the upstream API returns a non-2xx status.
        """
        ...

    async def chat_completion_stream(
        self,
        model_id: str,
        request: ChatCompletionRequest,
    ) -> AsyncGenerator[ChatCompletionStreamChunk, None]:
        """Stream a chat completion response token-by-token.

        Args:
            model_id: The model identifier to route this request to.
            request: The structured chat completion request.

        Yields:
            ChatCompletionStreamChunk instances as they arrive from upstream.

        Raises:
            ProviderError: If the upstream API returns a non-2xx status.
        """
        ...
        yield  # make this an async generator
```

## Type Guards

Use type guards when narrowing union types from parsed API responses:

```python
from typing import TypeGuard


def is_tool_call_chunk(
    chunk: ChatCompletionStreamChunk,
) -> TypeGuard[ChatCompletionStreamChunk]:
    """Return True when the stream chunk contains a tool-call delta."""
    return (
        bool(chunk.choices)
        and chunk.choices[0].delta is not None
        and chunk.choices[0].delta.tool_calls is not None
    )
```

## Logging Conventions

All providers must use structured key-value logging — never f-strings:

```python
from ogx.log import get_logger

logger = get_logger(__name__)

# Correct
logger.info("Sending request", model=model_id, tokens=request.max_tokens)

# Wrong — fails the pre-commit f-string logging check
logger.info(f"Sending request to {model_id}")
```

## Error Messages

All error messages must start with `"Failed to "`:

```python
raise ProviderError(f"Failed to authenticate with MyProvider: {status_code=}")
raise ValueError(f"Failed to parse stream chunk: unexpected format {raw_chunk!r}")
```

## Checklist Before Opening a PR

- [ ] All `Field` attributes in config class have a `description`
- [ ] `async chat_completion` and `async chat_completion_stream` are both implemented
- [ ] Provider spec added to `src/ogx/providers/registry/`
- [ ] No f-strings in `logger.*` calls
- [ ] All error messages start with `"Failed to "`
- [ ] `uv run mypy src/ogx/providers/remote/my_provider/` passes
- [ ] Integration test recording committed
