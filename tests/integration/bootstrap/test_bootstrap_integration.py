"""Bootstrap Service integration tests."""

from __future__ import annotations

from pathlib import Path

from vibe.bootstrap.service import BootstrapService
from vibe.bootstrap.state import BootstrapState
from vibe.logging.handlers import PLATFORM_LOG_FILE, log_directory


def test_integration_initializes_real_services(tmp_path: Path) -> None:
    """Bootstrap initializes real Configuration and Logging services."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()

    assert result.state == BootstrapState.RUNNING
    assert service.is_running is True
    assert service.configuration_service.is_initialized is True
    assert service.logging_service.is_initialized is True
    service.shutdown()
    assert service.state == BootstrapState.STOPPED


def test_integration_emits_startup_diagnostics(tmp_path: Path) -> None:
    """Bootstrap emits startup diagnostics through the platform logger."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()
    service.logging_service.get_logger("bootstrap").info("post-startup check")
    service.shutdown()

    log_contents = (log_directory(tmp_path) / PLATFORM_LOG_FILE).read_text(encoding="utf-8")
    assert "Bootstrap startup initiated" in log_contents
    assert "Configuration service initialized" in log_contents
    assert "Logging service initialized" in log_contents
    assert "Platform services registered" in log_contents
    assert "Lifecycle management available" in log_contents
    assert "Platform running" in log_contents


def test_integration_shutdown_after_running(tmp_path: Path) -> None:
    """Bootstrap shuts down an operational platform cleanly."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()
    configuration = service.configuration_service
    logging = service.logging_service
    logger = logging.get_logger("cli")
    logger.info("integration command executed")
    service.shutdown()

    assert service.is_running is False
    assert configuration.is_initialized is False
    assert logging.is_initialized is False
