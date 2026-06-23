"""Shared validation helpers for OGX provider configuration."""
from typing import Any, Optional


def require_field(config: dict[str, Any], field: str, context: str) -> Any:
    """Extract a required field from a config dict, raising on absence.

    Args:
        config: Configuration dictionary to read from.
        field: The key to look up.
        context: Human-readable context for error messages (e.g., provider name).

    Returns:
        The non-None value for `field`.

    Raises:
        ValueError: If the field is missing or its value is None.
    """
    value = config.get(field)
    if value is None:
        raise ValueError(f"Failed to load {context}: required field '{field}' is missing.")
    return value


def validate_positive_int(value: Any, field: str, context: str) -> int:
    """Validate that a config value is a positive integer.

    Args:
        value: The raw config value.
        field: The field name for error messages.
        context: Human-readable context for error messages.

    Returns:
        The value cast to `int`.

    Raises:
        ValueError: If the value cannot be cast to `int` or is not positive.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Failed to configure {context}: field '{field}' must be an integer, got {value!r}."
        ) from e
    if int_value <= 0:
        raise ValueError(
            f"Failed to configure {context}: field '{field}' must be positive, got {int_value}."
        )
    return int_value


def normalize_url(url: Optional[str], field: str, context: str) -> str:
    """Validate and normalize a URL string.

    Args:
        url: The URL to validate.
        field: The field name for error messages.
        context: Human-readable context for error messages.

    Returns:
        The URL with trailing slash removed.

    Raises:
        ValueError: If `url` is None/empty or lacks an http/https scheme.
    """
    if not url:
        raise ValueError(
            f"Failed to configure {context}: field '{field}' is required."
        )
    url = url.strip().rstrip("/")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(
            f"Failed to configure {context}: '{field}' must start with http:// or https://."
        )
    return url
