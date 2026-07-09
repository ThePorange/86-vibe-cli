"""Correlation identifier context management."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Self

_state = threading.local()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation identifier for the current execution context."""
    _state.correlation_id = correlation_id


def get_correlation_id() -> str | None:
    """Return the correlation identifier for the current execution context."""
    return getattr(_state, "correlation_id", None)


def clear_correlation_id() -> None:
    """Clear the correlation identifier for the current execution context."""
    if hasattr(_state, "correlation_id"):
        delattr(_state, "correlation_id")


class CorrelationContext:
    """Context manager for scoped correlation identifiers."""

    def __init__(self, correlation_id: str) -> None:
        self._correlation_id = correlation_id
        self._previous: str | None = None

    def __enter__(self) -> Self:
        self._previous = get_correlation_id()
        set_correlation_id(self._correlation_id)
        return self

    def __exit__(self, *_args: object) -> None:
        if self._previous is None:
            clear_correlation_id()
        else:
            set_correlation_id(self._previous)


@contextmanager
def correlation_context(correlation_id: str) -> Iterator[None]:
    """Yield a scoped correlation identifier context."""
    with CorrelationContext(correlation_id):
        yield
