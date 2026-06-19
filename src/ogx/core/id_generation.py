# Copyright (c) The OGX Contributors.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""Utilities for generating and overriding object identifiers.

By default, object IDs are produced by a caller-supplied *factory* callable so
that each subsystem can choose its own ID scheme (UUID, ULID, sequential int,
etc.).  Tests can install an :data:`IdOverride` via :func:`set_id_override` to
produce predictable, deterministic identifiers without touching the production
path.

Typical test usage::

    def my_override(kind: str, factory: IdFactory) -> str:
        return f"{kind}-0001"

    previous = set_id_override(my_override)
    try:
        # ... run test ...
    finally:
        reset_id_override(previous)
"""

from collections.abc import Callable

IdFactory = Callable[[], str]
"""A zero-argument callable that returns a fresh unique string identifier."""

IdOverride = Callable[[str, IdFactory], str]
"""A callable that receives the object *kind* and the default :data:`IdFactory`
and returns the identifier to use instead.  Installed globally via
:func:`set_id_override` for deterministic ID generation in tests.
"""

_id_override: IdOverride | None = None


def generate_object_id(kind: str, factory: IdFactory) -> str:
    """Generate an identifier for an object of the given *kind*.

    If an override has been installed with :func:`set_id_override`, that
    callable is invoked and its return value is used.  Otherwise *factory* is
    called directly to produce the ID.

    Args:
        kind: A short string that identifies the type of object being created
            (e.g. ``"response"`` or ``"item"``).  Passed verbatim to the
            override so it can generate type-specific identifiers.
        factory: A zero-argument callable that returns a fresh unique string
            when no override is active.

    Returns:
        The identifier to assign to the new object.
    """
    override = _id_override
    if override is not None:
        return override(kind, factory)
    return factory()


def set_id_override(override: IdOverride) -> IdOverride | None:
    """Install a global override for object ID generation.

    Replaces the current override (if any) and returns the previous value so
    that callers can restore it in a ``finally`` block or via
    :func:`reset_id_override`.

    Args:
        override: A callable conforming to :data:`IdOverride` that will be
            invoked by :func:`generate_object_id` instead of the default
            factory.

    Returns:
        The previously installed override, or ``None`` if none was set.
    """
    global _id_override  # noqa: PLW0603

    previous = _id_override
    _id_override = override
    return previous


def reset_id_override(previous: IdOverride | None) -> None:
    """Restore a previously saved ID override.

    Intended to be called in a ``finally`` block after :func:`set_id_override`
    to guarantee the global state is always restored even if the test raises.

    Args:
        previous: The value returned by the matching :func:`set_id_override`
            call.  May be ``None`` if no override was active before.
    """
    global _id_override  # noqa: PLW0603
    _id_override = previous
