# OGX Structured Logging Guide

OGX uses structured logging via `ogx.log`. All log calls must use keyword-value
format — never f-strings or %-style formatting. The pre-commit hook
`Block f-string logging` enforces this and will reject commits that use them.

## Import Pattern

```python
from ogx.log import get_logger

logger = get_logger(__name__)
```

Always use `__name__` so log lines include the module path, which makes
filtering by component easy in production log aggregators.

## Correct vs Incorrect

```python
# CORRECT: keyword-value pairs
logger.info("Processing request", model=model_id, provider=provider, tokens=n)
logger.warning("Rate limit hit", provider=provider, retry_after=retry_after)
logger.error("Failed to connect", host=host, port=port, error=str(e))

# WRONG: f-strings (blocked by pre-commit)
logger.info(f"Processing request for {model_id}")       # rejected
logger.warning("Rate limit: retry after %s", retry_after)  # rejected
logger.error("Failed: " + str(e))                         # rejected
```

## Log Levels

| Level     | When to use                                              |
|-----------|----------------------------------------------------------|
| `debug`   | Internal state changes during normal operation           |
| `info`    | Request lifecycle events (start, complete, routed)       |
| `warning` | Recoverable issues (rate limit, fallback triggered)      |
| `error`   | Failures that need attention (provider down, auth error) |
| `critical`| Service cannot continue (DB unreachable, config corrupt) |

## Request Tracing

Include `request_id` in all log lines within a request scope so traces
can be correlated across multiple log entries:

```python
async def handle_completion(request: CompletionRequest, request_id: str) -> CompletionResponse:
    logger.info("Completion started", request_id=request_id, model=request.model)
    try:
        response = await route_to_provider(request)
        logger.info(
            "Completion finished",
            request_id=request_id,
            model=request.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        return response
    except Exception as e:
        logger.error(
            "Completion failed",
            request_id=request_id,
            model=request.model,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
```

## Error Logging

Always include `error=str(e)` and `error_type=type(e).__name__`. Do not log
the full stack trace at `error` level — use `logger.exception()` only when
you want the traceback captured automatically:

```python
try:
    result = await provider.complete(request)
except ProviderError as e:
    # Include context fields so the error is actionable without the traceback.
    logger.error(
        "Failed to complete request",
        provider=provider.name,
        model=request.model,
        error=str(e),
        error_type=type(e).__name__,
        status_code=getattr(e, "status_code", None),
    )
    raise
```

## Performance Logging

For latency-sensitive paths, log timing with the `duration_ms` key:

```python
import time

start = time.monotonic()
result = await embed(text)
duration_ms = int((time.monotonic() - start) * 1000)

logger.info(
    "Embedding complete",
    model=model_id,
    input_chars=len(text),
    duration_ms=duration_ms,
)
```

## Provider Implementation Logging

Every provider adapter should log at entry and exit of the provider call:

```python
class MyProvider:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.logger.debug(
            "Sending request to provider",
            provider="my_provider",
            model=request.model,
            message_count=len(request.messages),
        )
        response = await self._send(request)
        self.logger.debug(
            "Received response from provider",
            provider="my_provider",
            model=request.model,
            finish_reason=response.choices[0].finish_reason,
        )
        return response
```

## Checking for Violations Locally

Run `scripts/check_logging.sh` before committing to catch f-string
logging violations before the pre-commit hook does:

```bash
bash scripts/check_logging.sh
```
