"""Health check endpoint implementation for the OGX API server.

Exposes ``GET /health`` returning the server version, uptime, and
provider availability status.
"""

from __future__ import annotations

import time
from typing import Any

_START_TIME: float = time.monotonic()


def get_uptime_seconds() -> float:
    """Return the number of seconds the server has been running.

    Returns:
        Elapsed wall-clock seconds since the module was first imported.
    """
    return time.monotonic() - _START_TIME


def build_health_response(
    version: str,
    providers: dict[str, bool],
) -> dict[str, Any]:
    """Build the JSON body for the ``/health`` endpoint.

    Args:
        version: The OGX server version string (e.g. ``'0.1.0'``).
        providers: Mapping from provider name to availability flag.

    Returns:
        A dict ready to be serialised as the HTTP response body.
    """
    return {
        "status": "ok" if all(providers.values()) else "degraded",
        "version": version,
        "uptime_seconds": round(get_uptime_seconds(), 3),
        "providers": {name: "up" if ok else "down" for name, ok in providers.items()},
    }
