# Copyright (c) The OGX Contributors.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import contextvars
import json
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, cast

from starlette.types import Scope

from ogx.core.datatypes import User
from ogx.log import get_logger

from .utils.dynamic import instantiate_class_type

if TYPE_CHECKING:
    from ogx_api import ProviderSpec

log = get_logger(name=__name__, category="core")

# Context variable for request provider data and auth attributes.
# Set at the start of each request and cleared when the request context exits.
PROVIDER_DATA_VAR: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "provider_data", default=None
)


class RequestProviderDataContext(AbstractContextManager[None]):
    """Context manager that installs per-request provider data into a context variable.

    Provider data is sourced from the ``X-OGX-Provider-Data`` request header and
    optionally supplemented with an authenticated ``User`` object.  The data is
    available to providers via :data:`PROVIDER_DATA_VAR` for the lifetime of the
    ``with`` block and is restored to its previous value on exit.

    Args:
        provider_data: Parsed JSON object from the provider-data header.  Must be
            a plain ``dict`` or ``None``; non-dict values are silently discarded.
        user: Authenticated user to embed under the ``"__authenticated_user"`` key
            so that providers can access auth info without a separate lookup.
    """

    def __init__(self, provider_data: dict[str, Any] | None = None, user: User | None = None) -> None:
        if provider_data is not None and not isinstance(provider_data, dict):
            log.error("Provider data must be a JSON object")
            provider_data = None
        self.provider_data: dict[str, Any] = provider_data or {}
        if user:
            self.provider_data["__authenticated_user"] = user

        self.token: contextvars.Token[dict[str, Any] | None] | None = None

    def __enter__(self) -> None:
        """Set the provider-data context variable and save the previous token."""
        self.token = PROVIDER_DATA_VAR.set(self.provider_data)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore the context variable to its value before ``__enter__`` was called."""
        if self.token is not None:
            PROVIDER_DATA_VAR.reset(self.token)


class NeedsRequestProviderData:
    """Mixin for providers that require per-request provider data from request headers.

    Providers that subclass this mixin gain access to :meth:`get_request_provider_data`,
    which reads :data:`PROVIDER_DATA_VAR` and validates its contents against the
    provider-specific validator class declared on the provider spec.

    The ``__provider_spec__`` class attribute must be set before calling
    :meth:`get_request_provider_data`; this is handled automatically by the
    provider registration machinery.
    """

    __provider_spec__: "ProviderSpec"

    def get_request_provider_data(self) -> Any:
        """Return validated per-request provider data for this provider.

        Reads the current :data:`PROVIDER_DATA_VAR` context variable, instantiates
        the validator declared on the provider spec, and returns the validated object.

        Returns:
            A validated provider-data object (type depends on the provider's
            ``provider_data_validator``), or ``None`` if no provider data is present
            in the current request context.

        Raises:
            ValueError: If the provider spec is not set, or if the spec does not
                declare a ``provider_data_validator``.
        """
        spec = self.__provider_spec__  # type: ignore[attr-defined]
        if not spec:
            raise ValueError(f"Provider spec not set on {self.__class__}")

        provider_type = spec.provider_type
        validator_class = spec.provider_data_validator
        if not validator_class:
            raise ValueError(f"Provider {provider_type} does not have a validator")

        val = PROVIDER_DATA_VAR.get()
        if not val:
            return None

        validator = instantiate_class_type(validator_class)  # type: ignore[no-untyped-call]
        try:
            provider_data = validator(**val)
            return provider_data
        except Exception as e:
            log.error(f"Error parsing provider data: {e}")
            return None


def parse_request_provider_data(headers: dict[str, str]) -> dict[str, Any] | None:
    """Extract and parse provider data from HTTP request headers.

    Looks for the ``X-OGX-Provider-Data`` header (case-insensitive) and decodes
    its JSON value.  The decoded value must be a JSON object (``dict``); scalar
    values and arrays are rejected.

    Args:
        headers: A mapping of header name to value.  Both the canonical
            (``X-OGX-Provider-Data``) and lower-case (``x-ogx-provider-data``)
            variants are accepted.

    Returns:
        A ``dict`` containing the parsed provider data, or ``None`` if the header
        is absent, empty, or contains an invalid value.
    """
    keys = [
        "X-OGX-Provider-Data",
        "x-ogx-provider-data",
    ]
    val: str | None = None
    for key in keys:
        val = headers.get(key, None)
        if val:
            break

    if not val:
        return None

    try:
        parsed = json.loads(val)
    except json.JSONDecodeError:
        log.error("Provider data not encoded as a JSON object!")
        return None

    if parsed is None:
        return None

    if not isinstance(parsed, dict):
        log.error("Provider data must be encoded as a JSON object")
        return None

    return cast(dict[str, Any], parsed)


def request_provider_data_context(
    headers: dict[str, str],
    user: User | None = None,
) -> AbstractContextManager[None]:
    """Build a context manager that sets per-request provider data for the duration of a block.

    This is the primary entry point used by request middleware.  It parses
    provider data out of the supplied headers and returns a
    :class:`RequestProviderDataContext` that installs it into
    :data:`PROVIDER_DATA_VAR`.

    Args:
        headers: HTTP request headers as a plain ``dict``.  The
            ``X-OGX-Provider-Data`` header is extracted if present.
        user: Authenticated user to embed in the provider data context so
            downstream providers can access it without a separate lookup.

    Returns:
        A context manager that sets the provider-data context variable on
        ``__enter__`` and restores it on ``__exit__``.
    """
    provider_data = parse_request_provider_data(headers)
    return RequestProviderDataContext(provider_data, user)


def get_authenticated_user() -> User | None:
    """Retrieve the authenticated user from the current request context.

    Returns:
        The :class:`~ogx.core.datatypes.User` embedded in the provider data
        context by :class:`RequestProviderDataContext`, or ``None`` if no user
        is present (e.g. auth is disabled, or called outside a request context).
    """
    provider_data = PROVIDER_DATA_VAR.get()
    if not provider_data:
        return None
    return provider_data.get("__authenticated_user")


def user_from_scope(scope: Scope) -> User | None:
    """Construct a :class:`~ogx.core.datatypes.User` from ASGI scope data.

    Authentication middleware populates ``scope["principal"]`` and
    ``scope["user_attributes"]`` after validating credentials.  This helper
    reads those values and assembles them into a ``User`` object.

    Args:
        scope: The ASGI connection scope dictionary, as passed to middleware
            and route handlers by Starlette / uvicorn.

    Returns:
        A :class:`~ogx.core.datatypes.User` built from ``scope["principal"]``
        and ``scope["user_attributes"]``, or ``None`` if both are absent
        (indicating that authentication is not enabled).
    """
    user_attributes: dict[str, Any] = scope.get("user_attributes", {})
    principal: str = scope.get("principal", "")

    # Auth not enabled: both fields will be empty / missing.
    if not principal and not user_attributes:
        return None

    return User(principal=principal, attributes=user_attributes)
