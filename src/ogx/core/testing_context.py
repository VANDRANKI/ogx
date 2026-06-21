# Copyright (c) The OGX Contributors.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""Test-context helpers for the OGX integration-test recording/replay system.

The module provides a lightweight ContextVar-based mechanism for propagating a
test identifier ("test context") through an async call stack.  The identifier
is used by the recording layer to key HTTP recordings so that concurrent tests
do not interfere with each other.

Typical usage (library mode)::

    token = set_test_context("my_test_id")
    try:
        ...  # code under test
    finally:
        reset_test_context(token)

In server mode the context is populated automatically via
``sync_test_context_from_provider_data`` when the ``OGX_TEST_INFERENCE_MODE``
environment variable is set.
"""

import os
from contextvars import ContextVar, Token

from ogx.core.request_headers import PROVIDER_DATA_VAR

TEST_CONTEXT: ContextVar[str | None] = ContextVar("ogx_test_context", default=None)


def get_test_context() -> str | None:
    """Get the current test context identifier.

    Returns:
        The test context string, or None if not set.
    """
    return TEST_CONTEXT.get()


def set_test_context(value: str | None) -> Token[str | None]:
    """Set the test context identifier for the current async context.

    Args:
        value: The test context string to set, or None to clear.

    Returns:
        A token that can be used to reset the context variable via
        :func:`reset_test_context`.
    """
    return TEST_CONTEXT.set(value)


def reset_test_context(token: Token[str | None]) -> None:
    """Reset the test context to its previous value using a token from set_test_context.

    Args:
        token: The token returned by a previous :func:`set_test_context` call.
    """
    TEST_CONTEXT.reset(token)


def sync_test_context_from_provider_data() -> Token[str | None] | None:
    """Sync test context from provider data when running in server test mode.

    This is a no-op unless both of the following conditions are met:

    1. The ``OGX_TEST_INFERENCE_MODE`` environment variable is set.
    2. The ``OGX_TEST_STACK_CONFIG_TYPE`` environment variable equals ``"server"``.

    Returns:
        A :class:`contextvars.Token` if the context was updated, or ``None``
        if the conditions above are not met or the provider data does not
        contain a ``__test_id`` key.
    """
    if "OGX_TEST_INFERENCE_MODE" not in os.environ:
        return None

    stack_config_type = os.environ.get("OGX_TEST_STACK_CONFIG_TYPE", "library_client")
    if stack_config_type != "server":
        return None

    try:
        provider_data = PROVIDER_DATA_VAR.get()
    except LookupError:
        provider_data = None

    if provider_data and "__test_id" in provider_data:
        return TEST_CONTEXT.set(provider_data["__test_id"])

    return None


def is_debug_mode() -> bool:
    """Check if test recording debug mode is enabled via OGX_TEST_DEBUG env var."""
    return os.environ.get("OGX_TEST_DEBUG", "").lower() in ("1", "true", "yes")
