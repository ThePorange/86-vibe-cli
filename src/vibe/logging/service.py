"""Logging Service orchestration and public API."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from vibe.configuration.service import ConfigurationService
from vibe.logging.correlation import (
    clear_correlation_id,
    get_correlation_id,
    set_correlation_id,
)
from vibe.logging.exceptions import (
    LoggerConfigurationError,
    LoggerInitializationError,
    LoggerShutdownError,
)
from vibe.logging.handlers import HandlerSet, attach_handlers, create_handlers
from vibe.logging.levels import LEVEL_NAMES, parse_level, register_trace_level
from vibe.logging.logger import PlatformLogger
from vibe.logging.models import LoggingConfig

_ROOT_LOGGER_NAME = "vibe"


class LoggingService:
    """Centralized logging for the 86-vibe platform."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        *,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the logging service.

        Args:
            configuration_service:
                Configuration service supplying logging settings.
            project_root:
                Optional project root used for log directory discovery.
        """
        self._configuration_service = configuration_service
        self._project_root = project_root or Path.cwd()
        self._config = LoggingConfig()
        self._level_name = "INFO"
        self._minimum_level = parse_level("INFO")
        self._loggers: dict[str, PlatformLogger] = {}
        self._handler_set: HandlerSet | None = None
        self._root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        self._initialized = False
        self._lock = threading.RLock()
        register_trace_level()

    def initialize(self) -> None:
        """Initialize logging outputs and levels."""
        with self._lock:
            if self._initialized:
                return
            try:
                self._config = self._load_logging_config()
                self._level_name = self._config.level
                self._minimum_level = parse_level(self._level_name)
                self._handler_set = create_handlers(
                    project_root=self._project_root,
                    console_enabled=self._config.console,
                    file_enabled=self._config.file,
                    debug_enabled=self._config.debug,
                    rotation_enabled=self._config.rotation,
                    colored_console=self._config.colored,
                    console_level=self._config.console_level,
                    file_level=self._config.file_level,
                )
                attach_handlers(self._root_logger, self._handler_set)
            except LoggerConfigurationError as exc:
                raise LoggerInitializationError(str(exc)) from exc
            except OSError as exc:
                raise LoggerInitializationError("Failed to initialize logging outputs.") from exc
            self._initialized = True

    def get_logger(self, name: str) -> PlatformLogger:
        """Return a logger for the given component name.

        Args:
            name:
                Logical component name.

        Returns:
            A platform logger instance.
        """
        with self._lock:
            if name not in self._loggers:
                child_logger = self._root_logger.getChild(name)
                self._loggers[name] = PlatformLogger(name, child_logger, self._minimum_level)
            return self._loggers[name]

    def set_level(self, level: str) -> None:
        """Set the default logging level.

        Args:
            level:
                Logging level name.

        Raises:
            LoggerConfigurationError:
                When the level name is not supported.
        """
        with self._lock:
            self._level_name = level.upper()
            self._minimum_level = parse_level(self._level_name)
            for platform_logger in self._loggers.values():
                platform_logger._minimum_level = self._minimum_level

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the active correlation identifier."""
        set_correlation_id(correlation_id)

    def get_correlation_id(self) -> str | None:
        """Return the active correlation identifier."""
        return get_correlation_id()

    def clear_correlation_id(self) -> None:
        """Clear the active correlation identifier."""
        clear_correlation_id()

    def flush(self) -> None:
        """Flush pending log events."""
        with self._lock:
            if self._handler_set is not None:
                self._handler_set.flush()

    def shutdown(self) -> None:
        """Flush and release logging resources."""
        with self._lock:
            try:
                self.flush()
                if self._handler_set is not None:
                    self._handler_set.close()
                    self._handler_set = None
                self._root_logger.handlers.clear()
                self._loggers.clear()
            except OSError as exc:
                raise LoggerShutdownError("Failed to shut down logging service.") from exc
            finally:
                self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the service has been initialized."""
        with self._lock:
            return self._initialized

    @property
    def supported_levels(self) -> tuple[str, ...]:
        """Return supported platform log level names."""
        return LEVEL_NAMES

    def _load_logging_config(self) -> LoggingConfig:
        if not self._configuration_service.is_initialized:
            self._configuration_service.load()

        section = self._configuration_service.get_section("logging")
        level = str(section.get("level", "INFO")).upper()
        return LoggingConfig(
            level=level,
            console=bool(section.get("console", True)),
            file=bool(section.get("file", True)),
            debug=bool(section.get("debug", False)),
            rotation=bool(section.get("rotation", True)),
            colored=bool(section.get("colored", True)),
            console_level=str(section.get("console_level", level)).upper(),
            file_level=str(section.get("file_level", "DEBUG")).upper(),
        )
