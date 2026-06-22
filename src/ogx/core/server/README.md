# server

FastAPI server implementation for OGX.

## Directory Structure

```text
server/
  __init__.py
  server.py                    # Main FastAPI app, route dispatch, SSE streaming, lifespan
  auth.py                      # AuthenticationMiddleware (Bearer token validation)
  auth_providers.py            # Auth provider implementations (Kubernetes, custom endpoint)
  quota.py                     # QuotaMiddleware (rate limiting per client)
  metrics.py                   # RequestMetricsMiddleware (per-API request metrics)
  routes.py                    # Route initialization and matching from FastAPI routers
  fastapi_router_registry.py   # Auto-discovery of FastAPI routers from ogx_api packages
```

## How It Works

### Server Startup

1. `main()` in `server.py` resolves the config, creates a `StackApp` (subclass of `FastAPI`).
2. `StackApp.__init__` creates and initializes a `Stack` instance (provider resolution, resource registration).
3. The lifespan context starts background tasks (e.g., periodic registry refresh).

### Route Registration

Routes are defined as native FastAPI routers. `fastapi_router_registry.py` auto-discovers router factories by scanning `ogx_api.<api>.fastapi_routes` modules for `create_router` functions. At startup, `server.py` calls `build_fastapi_router()` for each enabled API and includes the resulting router in the FastAPI app. External APIs can also register router factories via `register_external_api_routers()`.

### Middleware

- **`RequestMetricsMiddleware`** (`metrics.py`): Tracks per-API request counts and latency metrics. Runs as the outermost middleware.
- **`AuthenticationMiddleware`** (`auth.py`): Validates Bearer tokens using a configured auth provider (Kubernetes, custom endpoint). Extracts user identity and attributes for access control. Endpoints can opt out by setting `openapi_extra={PUBLIC_ROUTE_KEY: True}` on their route.
- **`RouteAuthorizationMiddleware`** (`auth.py`): Enforces route-level access policies based on user roles.
- **`QuotaMiddleware`** (`quota.py`): Enforces per-client rate limits (separate limits for authenticated vs. anonymous). Uses KVStore for tracking request counts.
- **`ClientVersionMiddleware`** (`server.py`): Rejects requests from clients with incompatible major.minor versions.
- **`ProviderDataMiddleware`** (`server.py`): Sets up request context for provider data propagation and test context.

### Response Handling

- Non-streaming responses return JSON via FastAPI's standard response handling.
- Streaming responses use Server-Sent Events (SSE) via `StreamingResponse`, with `create_sse_event()` serializing each chunk.
- Exceptions are translated to appropriate HTTP status codes by `translate_exception()`.

## Request Flow

The following diagram shows the full lifecycle of an inbound API request from network to provider and back:

```
HTTP Request
    |
    v
[RequestMetricsMiddleware]   <- outermost; records start time, increments in-flight counter
    |
    v
[ClientVersionMiddleware]    <- rejects incompatible ogx-client versions (major.minor check)
    |
    v
[AuthenticationMiddleware]   <- validates Bearer token; populates request.state.user
    |                            (skipped for routes with PUBLIC_ROUTE_KEY)
    v
[RouteAuthorizationMiddleware] <- checks user roles against route access policy
    |
    v
[QuotaMiddleware]             <- enforces per-client rate limits via KVStore
    |
    v
[ProviderDataMiddleware]      <- attaches provider_data context for downstream handlers
    |
    v
FastAPI Route Handler         <- resolves the Stack, calls the appropriate API impl
    |
    v
Stack / Provider              <- dispatches to the configured inference/tool/vector provider
    |
    +--[non-streaming]--> JSON response via FastAPI
    |
    +--[streaming]-------> StreamingResponse (SSE)
                           Each chunk: create_sse_event() -> "data: {...}\n\n"
                           Final:       "data: [DONE]\n\n"
```

### Key design decisions

- **Middleware ordering matters.** Metrics must wrap everything to capture total latency including auth failures. Auth must run before quota so that anonymous and authenticated clients get separate rate limit buckets.
- **SSE framing is centralised.** All streaming endpoints go through `create_sse_event()` so the wire format stays consistent. Providers yield plain Python objects; the server layer handles serialisation.
- **Exceptions are translated at the boundary.** `translate_exception()` in `server.py` maps OGX-internal exceptions (e.g. `ProviderNotFound`, `AuthenticationError`) to the appropriate HTTP status codes and OpenAI-compatible error bodies. Providers should raise typed exceptions, not raw `HTTPException`.
- **Public routes opt out of auth explicitly.** Setting `openapi_extra={PUBLIC_ROUTE_KEY: True}` on a route handler signals to `AuthenticationMiddleware` to skip token validation. This prevents accidental exposure — the default is always authenticated.

## Architecture Notes

### Adding a new API endpoint

1. Define your route in `ogx_api/<api>/fastapi_routes.py` using a standard FastAPI `APIRouter`.
2. Expose a `create_router(stack: Stack) -> APIRouter` factory. The `fastapi_router_registry` will discover it automatically.
3. If the endpoint is public (health checks, OAuth callbacks), add `openapi_extra={PUBLIC_ROUTE_KEY: True}` to bypass auth middleware.
4. For streaming responses, use `StreamingResponse` and yield chunks through `create_sse_event()`.

### Adding a new auth provider

1. Implement the `AuthProvider` protocol in `auth_providers.py`.
2. Register the new provider type in the `resolve_auth_provider()` factory.
3. Configure it in the distribution YAML under `server.auth_provider`.

### Quota configuration

Rate limits are configured per-distribution in the YAML config under `server.quota`. The `QuotaMiddleware` reads these at startup and enforces them via the configured KVStore backend (in-memory for development, Redis for production).

```yaml
server:
  quota:
    authenticated_requests_per_minute: 600
    anonymous_requests_per_minute: 60
```
