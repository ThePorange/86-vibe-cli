"""Logging Service tests."""

from __future__ import annotations

from vibe.configuration.service import ConfigurationService
from vibe.logging.service import LoggingService


def test_logging_service_initializes_from_configuration() -> None:
    """Logging service reads configuration during initialization."""
    configuration = ConfigurationService()
    configuration.load()
    logging_service = LoggingService(configuration)
    logging_service.initialize()
    assert logging_service.is_initialized is True


def test_logging_service_returns_named_logger() -> None:
    """Logging service provides component loggers."""
    configuration = ConfigurationService()
    configuration.load()
    logging_service = LoggingService(configuration)
    logging_service.initialize()
    logger = logging_service.get_logger("cli")
    logger.info("test message")
    assert logger is logging_service.get_logger("cli")


def test_logging_service_redacts_secret_fields() -> None:
    """Secret-like structured fields are redacted."""
    configuration = ConfigurationService()
    configuration.load()
    logging_service = LoggingService(configuration)
    logging_service.initialize()
    logger = logging_service.get_logger("security")
    message = logger._format_message("auth", {"api_key": "secret-value"})
    assert "secret-value" not in message
    assert "********" in message
