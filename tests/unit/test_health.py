"""Unit tests for ogx.core.health."""

import pytest
from unittest.mock import patch


def test_build_health_response_all_up():
    from ogx.core.health import build_health_response

    result = build_health_response("0.1.0", {"openai": True, "bedrock": True})
    assert result["status"] == "ok"
    assert result["version"] == "0.1.0"
    assert result["providers"]["openai"] == "up"
    assert result["providers"]["bedrock"] == "up"
    assert isinstance(result["uptime_seconds"], float)


def test_build_health_response_degraded():
    from ogx.core.health import build_health_response

    result = build_health_response("0.1.0", {"openai": True, "bedrock": False})
    assert result["status"] == "degraded"
    assert result["providers"]["bedrock"] == "down"


def test_build_health_response_empty_providers():
    from ogx.core.health import build_health_response

    result = build_health_response("0.1.0", {})
    assert result["status"] == "ok"
    assert result["providers"] == {}
