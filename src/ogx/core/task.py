# Copyright (c) The OGX Contributors.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""Utilities for propagating request context through async background tasks.

Background workers are long-lived asyncio tasks whose ContextVars are frozen
at creation time.  Without explicit propagation, every DB write from a worker
would be attributed to the wrong trace and the wrong user identity.

This module provides two complementary helpers:

* :class:`RequestContext` / :func:`capture_request_context` — snapshot the
  OTel trace context and provider auth data at *enqueue* time so they can be
  reinstated per work item.
* :func:`create_detached_background_task` — create a long-lived asyncio task
  that starts with a *clean* context so it does not permanently inherit the
  spawning request's identity.
"""

import asyncio
from collections.abc import Coroutine, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from opentelemetry import context as otel_context

from ogx.core.request_headers import PROVIDER_DATA_VAR


@dataclass
class RequestContext:
    """Snapshot of request-scoped state for propagation through background queues.

    Background workers are long-lived asyncio tasks whose contextvars are frozen
    at creation time.  Capturing both the OTel trace context and the provider /
    auth data at *enqueue* time and re-activating them per work-item ensures:

    * Each DB write is attributed to the correct request trace (OTel).
    * Each DB write is stamped with the correct user identity (PROVIDER_DATA_VAR).

    Attributes:
        otel_ctx: The OpenTelemetry context at the time of capture.
        provider_data: The provider / auth data stored in
            :data:`~ogx.core.request_headers.PROVIDER_DATA_VAR` at the time of
            capture.
    """

    otel_ctx: otel_context.Context
    provider_data: Any


def capture_request_context() -> RequestContext:
    """Snapshot the current request-scoped context for later use in a worker.

    Returns:
        A :class:`RequestContext` containing the current OTel context and
        provider auth data.  The snapshot is a plain dataclass with no live
        references, so it is safe to enqueue and restore in a different task.
    """
    return RequestContext(
        otel_ctx=otel_context.get_current(),
        provider_data=PROVIDER_DATA_VAR.get(),
    )


@contextmanager
def activate_request_context(ctx: RequestContext) -> Generator[None, None, None]:
    """Temporarily restore a previously captured request context.

    Use this in worker loops that run with a detached (empty) context to
    attribute work back to the originating request.  Both the OTel trace token
    and the provider auth data are restored on entry and reverted on exit,
    even if an exception is raised inside the ``with`` block.

    Args:
        ctx: A :class:`RequestContext` produced by
            :func:`capture_request_context` in the originating request handler.

    Yields:
        ``None`` — the context manager yields control back to the caller
        without producing a value.
    """
    otel_token = otel_context.attach(ctx.otel_ctx)
    provider_token = PROVIDER_DATA_VAR.set(ctx.provider_data)
    try:
        yield
    finally:
        PROVIDER_DATA_VAR.reset(provider_token)
        otel_context.detach(otel_token)


def create_detached_background_task(coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
    """Create an asyncio task that does not inherit request-scoped context.

    :func:`asyncio.create_task` copies all ContextVars at creation time, which
    causes long-lived background workers to permanently inherit the spawning
    request's OTel trace and auth identity.  This helper temporarily clears
    both before creating the task, then immediately restores them so the caller
    is unaffected.

    Args:
        coro: The coroutine to schedule as a background task.  It should use
            :func:`activate_request_context` internally to reinstate the correct
            context per work item.

    Returns:
        A new :class:`asyncio.Task` running *coro* with a clean context.
    """
    otel_token = otel_context.attach(otel_context.Context())
    provider_token = PROVIDER_DATA_VAR.set(None)
    try:
        task = asyncio.create_task(coro)
    finally:
        PROVIDER_DATA_VAR.reset(provider_token)
        otel_context.detach(otel_token)
    return task
