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

# Context variable for request provider data and auth attributes
PROVIDER_DATA_VAR: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("provider_data", default=None)


class RequestProviderDataContext(AbstractContextManager[None]):
    """Context manager that stores per-request provider data in a ContextVar.

    On entry the given *provider_data* dict (and optional *user*) are pushed
    into :data:`PROVIDER_DATA_VAR` so that downstream code can retrieve them
    with :func:`get_authenticated_user` or via the :class:`NeedsRequestProviderData`
    mixin.  On exit the previous value is restored atomically via the
    ContextVar token mechanism.
    """

    def __init__(self, provider_data: dict[str, Any] | None = None, user: User | None = None) -> None:
        if provider_data is not None and not isinstance(provider_data, dict):
            log.error("Provider data must be a JSON object")
            provider_data = None
        self.provider_data = provider_data or {}
        if user:
            self.provider_data["__authenticated_user"] = user

        self.token: contextvars.Token[dict[str, Any] | None] | None = None

    def __enter__(self) -> None:
        # Save the current value and set the new one
        self.token = PROVIDER_DATA_VAR.set(self.provider_data)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Restore the previous value
        if self.token is not None:
            PROVIDER_DATA_VAR.reset(self.token)


class NeedsRequestProviderData:
    """Mixin for providers that require per-request provider data from request headers."""

    __provider_spec__: "ProviderSpec"

    def get_request_provider_data(self) -> Any:
        """Retrieve and validate per-request provider data for this provider.

        Returns:
            A validated provider-data object (type determined by the spec's
            ``provider_data_validator``), or ``None`` if no provider data is
            present in the current request context.

        Raises:
            ValueError: If ``__provider_spec__`` is not set on the instance, or
                if the spec does not declare a ``provider_data_validator``.
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
            log.error("Error parsing provider data", error=str(e))
            return None


def parse_request_provider_data(headers: dict[str, str]) -> dict[str, Any] | None:
    """Parse provider data from the ``X-OGX-Provider-Data`` request header.

    The header value must be a JSON-encoded object.  Both the canonical
    mixed-case form and the all-lowercase form of the header name are
    accepted because HTTP/2 normalises headers to lowercase.

    Args:
        headers: A mapping of header names to values, as provided by the
            ASGI framework.

    Returns:
        The parsed provider data dict, or ``None`` if the header is absent,
        empty, or not a valid JSON object.
    """
    keys = [
        "X-OGX-Provider-Data",
        "x-ogx-provider-data",
    ]
    val = None
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


def request_provider_data_context(headers: dict[str, str], user: User | None = None) -> AbstractContextManager[None]:
    """Build a context manager that injects provider data from request headers.

    Parses ``X-OGX-Provider-Data`` from *headers* and, together with the
    optional *user*, pushes the data into :data:`PROVIDER_DATA_VAR` for the
    duration of the context.

    Args:
        headers: Raw request headers mapping (case-sensitive; both
            ``X-OGX-Provider-Data`` and ``x-ogx-provider-data`` are checked).
        user: Authenticated user to embed in the provider data, if any.

    Returns:
        A :class:`RequestProviderDataContext` context manager ready to be used
        in an ``async with`` or ``with`` block.
    """
    provider_data = parse_request_provider_data(headers)
    return RequestProviderDataContext(provider_data, user)


def get_authenticated_user() -> User | None:
    """Retrieve the authenticated user from the current request context.

    Returns:
        The :class:`~ogx.core.datatypes.User` stored by the most recent
        :class:`RequestProviderDataContext`, or ``None`` if no context is
        active or no user was set.
    """
    provider_data = PROVIDER_DATA_VAR.get()
    if not provider_data:
        return None
    return provider_data.get("__authenticated_user")


def user_from_scope(scope: Scope) -> User | None:
    """Create a :class:`~ogx.core.datatypes.User` from ASGI scope data.

    Authentication middleware is expected to populate ``scope["principal"]``
    and ``scope["user_attributes"]`` before the route handler runs.  This
    helper reads those keys and constructs the corresponding User object.

    Args:
        scope: The ASGI connection scope dict.

    Returns:
        A :class:`~ogx.core.datatypes.User` if authentication data is present,
        or ``None`` when auth is disabled (both ``principal`` and
        ``user_attributes`` are absent / empty).
    """
    user_attributes = scope.get("user_attributes", {})
    principal = scope.get("principal", "")

    # auth not enabled
    if not principal and not user_attributes:
        return None

    return User(principal=principal, attributes=user_attributes)
