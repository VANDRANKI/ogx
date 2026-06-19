# Copyright (c) The OGX Contributors.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import os


class MissingCredentialError(Exception):
    """Raised when a required credential is not found in the environment.

    This exception is raised by :func:`get_env_or_fail` when the requested
    environment variable is either absent or set to an empty string.  Callers
    that cannot continue without the credential should let this propagate;
    callers that want to fall back to a default should catch it explicitly.
    """

    pass


def get_env_or_fail(key: str) -> str:
    """Return the value of an environment variable or raise a descriptive error.

    Looks up *key* in the current process environment.  If the variable is
    missing or empty, raises :exc:`MissingCredentialError` with actionable
    instructions so developers know exactly how to supply the missing value.

    Args:
        key: The name of the environment variable to look up.

    Returns:
        The non-empty string value of the environment variable.

    Raises:
        MissingCredentialError: If *key* is not set or is set to an empty
            string.  The error message lists three ways to supply the value:
            exporting in the shell, writing a ``.env`` file, or passing it
            directly to pytest.
    """
    value = os.getenv(key)
    if not value:
        raise MissingCredentialError(
            f"\nMissing {key} in environment. Please set it using one of these methods:"
            f"\n1. Export in shell: export {key}=your-key"
            f"\n2. Create .env file in project root with: {key}=your-key"
            f"\n3. Pass directly to pytest: pytest --env {key}=your-key"
        )
    return value
