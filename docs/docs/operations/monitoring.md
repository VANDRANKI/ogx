# Monitoring OGX

This page summarises the key operational signals available when running OGX in production.

## Health endpoint

See [Health Check](health-check.md) for the `/health` endpoint format and Kubernetes probe configuration.

## Logging

OGX uses structured key-value logging via `ogx.log`. All log lines include:

- `model` — the model identifier for the request
- `provider` — the resolved provider name
- `request_id` — unique per-request identifier

Set `LOG_LEVEL=debug` for verbose output during development.

## Metrics

Prometheus metrics are exposed at `/metrics` when the optional `prometheus-client` package is installed. Key metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `ogx_requests_total` | Counter | Total requests by model and status |
| `ogx_request_duration_seconds` | Histogram | End-to-end latency |
| `ogx_provider_errors_total` | Counter | Provider errors by type |

## Alerts

Recommended alert thresholds:

- `ogx_provider_errors_total` rate > 1% over 5 minutes — check provider availability
- `ogx_request_duration_seconds` p99 > 30s — possible provider timeout misconfiguration
