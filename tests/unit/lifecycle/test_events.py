"""Lifecycle event unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from vibe.lifecycle.events import LifecycleEvent, LifecycleEventDispatcher, LifecycleEventType
from vibe.lifecycle.state import ServiceLifecycleState


@dataclass
class _FakeLogger:
    messages: list[str] = field(default_factory=list)

    def error(self, message: str, **fields: object) -> None:
        self.messages.append(message)


def test_subscribers_receive_events_in_registration_order() -> None:
    """Lifecycle subscribers execute synchronously in registration order."""
    dispatcher = LifecycleEventDispatcher()
    received: list[str] = []

    def first_handler(event: LifecycleEvent) -> None:
        received.append("first")

    def second_handler(event: LifecycleEvent) -> None:
        received.append("second")

    dispatcher.subscribe(first_handler)
    dispatcher.subscribe(second_handler)
    dispatcher.publish(
        LifecycleEvent(
            event_type=LifecycleEventType.SERVICE_REGISTERED,
            service_id="example",
            previous_state=None,
            current_state=ServiceLifecycleState.REGISTERED,
            timestamp=datetime.now(UTC),
        )
    )
    assert received == ["first", "second"]


def test_subscriber_exceptions_are_isolated() -> None:
    """Subscriber failures do not prevent other subscribers from running."""
    logger = _FakeLogger()
    dispatcher = LifecycleEventDispatcher(logger=logger)  # type: ignore[arg-type]
    received: list[str] = []

    def failing_handler(_event: LifecycleEvent) -> None:
        raise RuntimeError("subscriber failed")

    def success_handler(_event: LifecycleEvent) -> None:
        received.append("ok")

    dispatcher.subscribe(failing_handler)
    dispatcher.subscribe(success_handler)
    dispatcher.publish(
        LifecycleEvent(
            event_type=LifecycleEventType.SERVICE_READY,
            service_id="example",
            previous_state=ServiceLifecycleState.REGISTERED,
            current_state=ServiceLifecycleState.READY,
            timestamp=datetime.now(UTC),
        )
    )
    assert received == ["ok"]
    assert logger.messages
