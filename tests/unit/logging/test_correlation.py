"""Correlation identifier unit tests."""

from __future__ import annotations

import threading

from vibe.logging.correlation import (
    CorrelationContext,
    clear_correlation_id,
    get_correlation_id,
    set_correlation_id,
)


def test_correlation_identifier_lifecycle() -> None:
    """Correlation identifiers can be set, retrieved, and cleared."""
    set_correlation_id("corr-123")
    assert get_correlation_id() == "corr-123"
    clear_correlation_id()
    assert get_correlation_id() is None


def test_correlation_context_restores_previous_value() -> None:
    """Nested correlation contexts restore the previous identifier."""
    set_correlation_id("outer")
    with CorrelationContext("inner"):
        assert get_correlation_id() == "inner"
    assert get_correlation_id() == "outer"
    clear_correlation_id()


def test_correlation_context_isolates_threads() -> None:
    """Correlation identifiers do not leak between threads."""
    barrier = threading.Barrier(2)
    results: dict[str, str | None] = {}

    def worker(name: str) -> None:
        with CorrelationContext(name):
            barrier.wait()
            results[name] = get_correlation_id()

    threads = [
        threading.Thread(target=worker, args=("thread-a",)),
        threading.Thread(target=worker, args=("thread-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results["thread-a"] == "thread-a"
    assert results["thread-b"] == "thread-b"
    assert get_correlation_id() is None
