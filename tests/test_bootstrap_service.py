"""Bootstrap Service tests."""

from __future__ import annotations

from vibe.bootstrap.service import BootstrapService, BootstrapStatus


def test_bootstrap_service_reaches_ready_state() -> None:
    """Bootstrap initializes configuration and logging services."""
    service = BootstrapService()
    service.bootstrap()
    assert service.is_ready() is True
    assert service.status() == BootstrapStatus.READY
    health = service.health()
    assert health.ready is True
    assert health.services["configuration"] == "ready"
    assert health.services["logging"] == "ready"


def test_bootstrap_service_is_idempotent() -> None:
    """Repeated bootstrap calls do not fail."""
    service = BootstrapService()
    service.bootstrap()
    service.bootstrap()
    assert service.is_ready() is True


def test_bootstrap_service_shutdown_resets_state() -> None:
    """Shutdown returns bootstrap to uninitialized state."""
    service = BootstrapService()
    service.bootstrap()
    service.shutdown()
    assert service.is_ready() is False
    assert service.status() == BootstrapStatus.UNINITIALIZED
