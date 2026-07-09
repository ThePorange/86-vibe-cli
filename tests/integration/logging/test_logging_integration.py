"""Logging Service integration tests."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from vibe.configuration.service import ConfigurationService
from vibe.logging.handlers import DEBUG_LOG_FILE, ERROR_LOG_FILE, PLATFORM_LOG_FILE, log_directory
from vibe.logging.service import LoggingService


def _integration_service(tmp_path: Path, **overrides: object) -> LoggingService:
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir(exist_ok=True)
    lines = [
        "logging:",
        "  level: INFO",
        "  console: false",
        "  file: true",
        "  debug: true",
        "  rotation: true",
    ]
    for key, value in overrides.items():
        if isinstance(value, bool):
            lines.append(f"  {key}: {'true' if value else 'false'}")
        else:
            lines.append(f"  {key}: {value}")
    (config_dir / "config.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    configuration = ConfigurationService(project_root=tmp_path)
    configuration.load()
    service = LoggingService(configuration, project_root=tmp_path)
    service.initialize()
    return service


def test_integration_reads_configuration_through_configuration_service(tmp_path: Path) -> None:
    """Logging configuration is consumed exclusively through Configuration Service."""
    service = _integration_service(tmp_path, level="WARNING")
    logger = service.get_logger("integration")
    logger.info("hidden info")
    logger.warning("visible warning")
    service.flush()

    contents = (log_directory(tmp_path) / PLATFORM_LOG_FILE).read_text(encoding="utf-8")
    assert "hidden info" not in contents
    assert "visible warning" in contents
    service.shutdown()


def test_integration_creates_required_log_files(tmp_path: Path) -> None:
    """Integration logging creates required platform log files."""
    service = _integration_service(tmp_path)
    logger = service.get_logger("filesystem")
    logger.debug("debug event")
    logger.error("error event")
    service.flush()

    log_dir = log_directory(tmp_path)
    assert log_dir.is_dir()
    assert (log_dir / PLATFORM_LOG_FILE).exists()
    assert (log_dir / ERROR_LOG_FILE).exists()
    assert (log_dir / DEBUG_LOG_FILE).exists()
    service.shutdown()


def test_integration_structured_and_exception_events(tmp_path: Path) -> None:
    """Structured and exception events are written to persistent logs."""
    service = _integration_service(tmp_path)
    logger = service.get_logger("events")
    logger.info("structured event", repository="86-vibe-cli", document_count=3)
    try:
        raise RuntimeError("integration failure")
    except RuntimeError:
        service.set_correlation_id("corr-integration")
        logger.exception("exception event", command="doctor")
    service.flush()

    platform_contents = (log_directory(tmp_path) / PLATFORM_LOG_FILE).read_text(encoding="utf-8")
    error_contents = (log_directory(tmp_path) / ERROR_LOG_FILE).read_text(encoding="utf-8")
    assert "structured event" in platform_contents
    assert "document_count=3" in platform_contents
    assert "exception event" in error_contents
    assert "corr-integration" in error_contents
    assert "RuntimeError" in error_contents
    service.shutdown()


def test_integration_rotation_creates_archive_files(tmp_path: Path) -> None:
    """Rotating handlers archive previous log files."""
    service = _integration_service(tmp_path)
    root_logger = logging.getLogger("vibe")
    rotating_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, RotatingFileHandler)
        and handler.baseFilename.endswith(PLATFORM_LOG_FILE)
    ]
    assert rotating_handlers
    handler = rotating_handlers[0]
    handler.maxBytes = 64
    handler.backupCount = 2

    logger = service.get_logger("rotation")
    for index in range(20):
        logger.info(f"rotation event {index} with additional payload")
    service.flush()
    handler.doRollover()
    service.flush()

    log_dir = log_directory(tmp_path)
    archived = list(log_dir.glob(f"{PLATFORM_LOG_FILE}.*"))
    assert archived
    service.shutdown()
