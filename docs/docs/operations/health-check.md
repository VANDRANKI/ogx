# Health Check

OGX exposes a ``GET /health`` endpoint that returns server status.

## Response format

```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 3600.123,
  "providers": {
    "openai": "up",
    "bedrock": "down"
  }
}
```

## Status values

| Field | Value | Meaning |
|-------|-------|---------|
| `status` | `"ok"` | All configured providers available |
| `status` | `"degraded"` | One or more providers unavailable |
| `providers[name]` | `"up"` | Provider responding normally |
| `providers[name]` | `"down"` | Provider not reachable |

## Usage with load balancers

Configure your load balancer to send periodic ``GET /health`` probes.
Return ``200`` for both ``ok`` and ``degraded`` states — the server is still
functional. Return ``503`` only if the server process itself cannot respond.

## Kubernetes readiness probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
