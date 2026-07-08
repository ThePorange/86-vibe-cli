"""Configuration Service tests."""

from __future__ import annotations

from vibe.configuration.service import ConfigurationService


def test_configuration_service_loads_defaults() -> None:
    """Configuration service exposes built-in defaults after load."""
    service = ConfigurationService()
    service.initialize()
    service.load()
    assert service.validate() is True
    assert service.get("platform.name") == "86-vibe"
    assert service.contains("logging.level") is True


def test_configuration_service_export_is_read_only_snapshot() -> None:
    """Exported configuration returns a structured snapshot."""
    service = ConfigurationService()
    service.load()
    exported = service.export()
    exported["platform"]["name"] = "changed"
    assert service.get("platform.name") == "86-vibe"


def test_configuration_service_shutdown_resets_state() -> None:
    """Shutdown releases runtime configuration."""
    service = ConfigurationService()
    service.load()
    service.shutdown()
    assert service.is_initialized is False
    assert service.export() == {}
