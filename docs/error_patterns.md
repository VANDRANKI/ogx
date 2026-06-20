# Error Patterns in OGX

Reference for provider and API developers on how to raise, wrap, and log
errors consistently.

---

## Raising errors

All errors **must** begin with `"Failed to "` per the coding guidelines:

```python
from ogx.log import get_logger

logger = get_logger(__name__)

def fetch_model_info(model_id: str) -> dict:
    """Retrieve model metadata from the provider."""
    try:
        response = _http_client.get(f"/models/{model_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Failed to fetch model info",
            model_id=model_id,
            status_code=exc.response.status_code,
        )
        raise ProviderError(
            f"Failed to fetch model info for '{model_id}': "
            f"HTTP {exc.response.status_code}"
        ) from exc
```

---

## Mapping provider HTTP errors to OGX types

| HTTP Status | OGX Exception | Use case |
|-------------|---------------|----------|
| 400 | `ValidationError` | Malformed request |
| 401 | `AuthenticationError` | Bad API key |
| 403 | `PermissionError` | Insufficient scope |
| 404 | `ModelNotFoundError` | Unknown model |
| 429 | `RateLimitError` | Quota exceeded |
| 5xx | `ProviderError` | Upstream failure |

```python
from ogx.api.errors import (
    AuthenticationError, ModelNotFoundError, RateLimitError, ProviderError
)

def _map_http_error(status_code: int, body: str, model: str) -> Exception:
    """Convert a provider HTTP error to the appropriate OGX exception."""
    if status_code == 401:
        return AuthenticationError(f"Failed to authenticate with provider: {body}")
    if status_code == 404:
        return ModelNotFoundError(f"Failed to find model '{model}': not available")
    if status_code == 429:
        return RateLimitError(f"Failed to call provider: rate limit exceeded")
    return ProviderError(f"Failed to call provider: HTTP {status_code} - {body}")
```

---

## Logging conventions

Use structured key-value logging — no f-strings in log calls:

```python
# Good
logger.info("Inference request completed", model=model_id, latency_ms=latency)

# Bad (blocked by pre-commit hook)
logger.info(f"Inference request for {model_id} completed in {latency}ms")
```
