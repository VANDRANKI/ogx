# Provider Validation Patterns

This guide describes the validation conventions used across OGX providers.

## 1. Config field validation

Provider config classes use Pydantic `Field` with `description` so documentation
is generated automatically.

```python
from pydantic import BaseModel, Field, model_validator

class MyProviderConfig(BaseModel):
    api_key: str = Field(description="API key for authentication.")
    base_url: str = Field(
        default="https://api.example.com",
        description="Base URL for API requests.",
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds (1-300).",
    )

    @model_validator(mode="after")
    def check_api_key_not_empty(self) -> "MyProviderConfig":
        if not self.api_key.strip():
            raise ValueError("Failed to initialise provider: api_key must not be empty")
        return self
```

## 2. Request validation helpers

Use `TypeGuard` functions to narrow request types before processing.

```python
from typing import TypeGuard
from ogx_api.types.responses import CreateResponseParams

def has_system_prompt(params: CreateResponseParams) -> TypeGuard[CreateResponseParams]:
    """Return True when params include at least one system message."""
    return any(
        getattr(msg, "role", None) == "system"
        for msg in (params.input or [])
    )
```

## 3. Error message conventions

All provider error messages must start with `"Failed to "` followed by a
verbose description to aid debugging.

```python
from ogx.log import get_logger

logger = get_logger(__name__)

def _call_api(endpoint: str) -> dict:
    try:
        return _http_get(endpoint)
    except TimeoutError as exc:
        raise RuntimeError(
            f"Failed to reach provider endpoint {endpoint}: request timed out after {timeout}s"
        ) from exc
```

## 4. Structured logging

Always use key-value style logging — no f-strings in log calls.

```python
# Good
logger.info("Processing inference request", model=model_id, provider=provider_type)

# Bad — triggers the pre-commit hook
logger.info(f"Processing {model_id} via {provider_type}")
```

## 5. Validation checklist

- [ ] Config class uses `Field(description=...)` for all fields
- [ ] Cross-field constraints in `@model_validator(mode="after")`
- [ ] Error messages start with `"Failed to ..."`
- [ ] No f-strings in `logger.*` calls
- [ ] `TypeGuard` functions narrow types before branching logic
