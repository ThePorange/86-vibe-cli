"""Logging Service unit tests."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import pytest

from vibe.configuration.service import ConfigurationService
from vibe.logging.exceptions import LoggerConfigurationError, LoggerInitializationError
from vibe.logging.handlers import ERROR_LOG_FILE, PLATFORM_LOG_FILE, log_directory
from vibe.logging.service import LoggingService


def _service(tmp_path: Path, **config_overrides: object) -> LoggingService:
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir(exist_ok=True)
    if config_overrides:
        lines = ["logging:"]
        for key, value in config_overrides.items():
            if isinstance(value, bool):
                lines.append(f"  {key}: {'true' if value else 'false'}")
            else:
                lines.append(f"  {key}: {value}")
        (config_dir / "config.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    configuration = ConfigurationService(project_root=tmp_path)
    configuration.load()
    return LoggingService(configuration, project_root=tmp_path)


def test_logging_service_initializes_from_configuration(tmp_path: Path) -> None:
    """Logging service reads configuration during initialization."""
    service = _service(tmp_path)
    service.initialize()
    assert service.is_initialized is True
    service.shutdown()


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    """Repeated initialization does not fail."""
    service = _service(tmp_path)
    service.initialize()
    service.initialize()
    assert service.is_initialized is True
    service.shutdown()


def test_invalid_configuration_raises_initialization_error(tmp_path: Path) -> None:
    """Invalid logging configuration fails deterministically."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "logging:\n  level: INFO\n  console_level: VERBOSE\n",
        encoding="utf-8",
    )
    configuration = ConfigurationService(project_root=tmp_path)
    configuration.load()
    service = LoggingService(configuration, project_root=tmp_path)
    with pytest.raises(LoggerInitializationError):
        service.initialize()


def test_logger_registry_returns_identical_instances(tmp_path: Path) -> None:
    """Identical logger names return the same instance."""
    service = _service(tmp_path)
    service.initialize()
    logger_a = service.get_logger("repository")
    logger_b = service.get_logger("repository")
    logger_c = service.get_logger("cli")
    assert logger_a is logger_b
    assert logger_a is not logger_c
    service.shutdown()


def test_set_level_updates_runtime_level(tmp_path: Path) -> None:
    """Configured levels can be updated at runtime."""
    service = _service(tmp_path)
    service.initialize()
    service.set_level("ERROR")
    assert service.get_logger("cli")._minimum_level == logging.ERROR
    service.shutdown()


def test_set_level_rejects_unknown_values(tmp_path: Path) -> None:
    """Unknown runtime levels raise configuration errors."""
    service = _service(tmp_path)
    service.initialize()
    with pytest.raises(LoggerConfigurationError):
        service.set_level("VERBOSE")
    service.shutdown()


def test_correlation_identifier_api(tmp_path: Path) -> None:
    """Logging service exposes correlation identifier management."""
    service = _service(tmp_path)
    service.initialize()
    service.set_correlation_id("corr-42")
    assert service.get_correlation_id() == "corr-42"
    service.clear_correlation_id()
    assert service.get_correlation_id() is None
    service.shutdown()


def test_shutdown_is_safe_to_call_multiple_times(tmp_path: Path) -> None:
    """Repeated shutdown calls remain safe."""
    service = _service(tmp_path)
    service.initialize()
    service.shutdown()
    service.shutdown()
    assert service.is_initialized is False


def test_file_logging_writes_platform_and_error_logs(tmp_path: Path) -> None:
    """File handlers write persistent log output."""
    service = _service(tmp_path, file=True, console=False, debug=True)
    service.initialize()
    logger = service.get_logger("cli")
    logger.info("info event", command="init")
    logger.error("error event")
    service.flush()

    platform_log = log_directory(tmp_path) / PLATFORM_LOG_FILE
    error_log = log_directory(tmp_path) / ERROR_LOG_FILE
    platform_contents = platform_log.read_text(encoding="utf-8")
    error_contents = error_log.read_text(encoding="utf-8")
    assert "info event" in platform_contents
    assert "error event" in error_contents
    service.shutdown()


def test_concurrent_logging_preserves_integrity(tmp_path: Path) -> None:
    """Concurrent logging does not corrupt output."""
    service = _service(tmp_path, console=False, file=True)
    service.initialize()
    logger = service.get_logger("concurrency")
    barrier = threading.Barrier(8)
    errors: list[str] = []

    def worker(index: int) -> None:
        barrier.wait()
        for _ in range(20):
            logger.info("event", index=index)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    service.flush()

    contents = (log_directory(tmp_path) / PLATFORM_LOG_FILE).read_text(encoding="utf-8")
    if contents.count("event") != 160:
        errors.append("unexpected event count")
    assert errors == []
    service.shutdown()
