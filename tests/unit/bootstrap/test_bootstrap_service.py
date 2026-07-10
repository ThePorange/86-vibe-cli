"""Bootstrap Service unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from vibe.bootstrap.exceptions import (
    BootstrapInitializationError,
    BootstrapShutdownError,
    BootstrapStateError,
)
from vibe.bootstrap.service import BootstrapService
from vibe.bootstrap.state import BootstrapState


@dataclass
class FakeConfigurationService:
    """Test double for Configuration Service lifecycle behavior."""

    initialized: bool = False
    loaded: bool = False
    valid: bool = True
    fail_initialize: bool = False
    fail_load: bool = False
    calls: list[str] = field(default_factory=list)

    def initialize(self) -> None:
        self.calls.append("initialize")
        if self.fail_initialize:
            raise RuntimeError("configuration initialize failed")
        self.initialized = True

    def load(self) -> None:
        self.calls.append("load")
        if self.fail_load:
            raise RuntimeError("configuration load failed")
        self.loaded = True
        self.initialized = True

    def validate(self) -> bool:
        self.calls.append("validate")
        return self.valid

    def get_section(self, section: str) -> dict[str, object]:
        self.calls.append(f"get_section:{section}")
        return {}

    def shutdown(self) -> None:
        self.calls.append("shutdown")
        self.initialized = False
        self.loaded = False

    @property
    def is_initialized(self) -> bool:
        return self.initialized


@dataclass
class FakeLoggingService:
    """Test double for Logging Service lifecycle behavior."""

    configuration_service: Any
    initialized: bool = False
    fail_initialize: bool = False
    fail_shutdown: bool = False
    calls: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def initialize(self) -> None:
        self.calls.append("initialize")
        if self.fail_initialize:
            raise RuntimeError("logging initialize failed")
        self.initialized = True

    def shutdown(self) -> None:
        self.calls.append("shutdown")
        if self.fail_shutdown:
            raise RuntimeError("logging shutdown failed")
        self.initialized = False

    def get_logger(self, name: str) -> _FakeLogger:
        return _FakeLogger(self.messages)

    @property
    def is_initialized(self) -> bool:
        return self.initialized


@dataclass
class _FakeLogger:
    messages: list[str]

    def info(self, message: str, **fields: object) -> None:
        self.messages.append(message)

    def error(self, message: str, **fields: object) -> None:
        self.messages.append(message)


def test_successful_initialization_order() -> None:
    """Bootstrap initializes configuration before logging."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    result = service.initialize()

    assert result.state == BootstrapState.RUNNING
    assert configuration.calls == ["initialize", "load", "validate", "get_section:lifecycle"]
    assert logging.calls == ["initialize"]
    assert service.is_running is True


def test_repeated_initialization_after_running_is_idempotent() -> None:
    """Repeated initialize calls do not reinitialize services."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    service.initialize()
    service.initialize()

    assert configuration.calls.count("load") == 1
    assert logging.calls.count("initialize") == 1


def test_initialization_failure_before_logging_raises(tmp_path: Path) -> None:
    """Startup failure before logging raises BootstrapInitializationError."""
    configuration = FakeConfigurationService(fail_load=True)
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    with pytest.raises(BootstrapInitializationError):
        service.initialize()

    assert service.state == BootstrapState.FAILED
    assert logging.calls == []


def test_initialization_failure_after_logging_attempts_safe_shutdown() -> None:
    """Startup failure after logging triggers safe shutdown."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration, fail_initialize=True)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    with pytest.raises(BootstrapInitializationError):
        service.initialize()

    assert service.state == BootstrapState.FAILED
    assert logging.calls == ["initialize"]


def test_initialize_from_failed_state_raises() -> None:
    """Failed bootstrap cannot be retried automatically."""
    configuration = FakeConfigurationService(fail_load=True)
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    with pytest.raises(BootstrapInitializationError):
        service.initialize()
    with pytest.raises(BootstrapStateError):
        service.initialize()


def test_successful_shutdown_order() -> None:
    """Bootstrap shuts down logging before configuration."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]
    service.initialize()
    service.shutdown()

    assert logging.calls[-1] == "shutdown"
    assert configuration.calls[-1] == "shutdown"
    assert service.state == BootstrapState.STOPPED


def test_shutdown_before_startup_is_safe() -> None:
    """Shutdown before startup returns successfully."""
    service = BootstrapService(
        FakeConfigurationService(),
        FakeLoggingService(FakeConfigurationService()),
    )  # type: ignore[arg-type]
    service.shutdown()
    assert service.state == BootstrapState.NOT_STARTED


def test_repeated_shutdown_is_idempotent() -> None:
    """Repeated shutdown calls remain safe."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]
    service.initialize()
    service.shutdown()
    service.shutdown()
    assert service.state == BootstrapState.STOPPED


def test_shutdown_failure_raises_bootstrap_shutdown_error() -> None:
    """Shutdown failures raise BootstrapShutdownError and enter FAILED state."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration, fail_shutdown=True)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]
    service.initialize()

    with pytest.raises(BootstrapShutdownError):
        service.shutdown()

    assert service.state == BootstrapState.FAILED


def test_service_accessors_require_running_state() -> None:
    """Service accessors raise before bootstrap completes."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]

    with pytest.raises(BootstrapStateError):
        _ = service.configuration_service
    with pytest.raises(BootstrapStateError):
        _ = service.logging_service
    with pytest.raises(BootstrapStateError):
        _ = service.service_registry
    with pytest.raises(BootstrapStateError):
        _ = service.lifecycle_manager

    service.initialize()
    assert service.configuration_service is configuration
    assert service.logging_service is logging
    assert service.service_registry.count == 5
    assert service.lifecycle_manager.status().service_count == 5


def test_bootstrap_alias_matches_initialize(tmp_path: Path) -> None:
    """Repository bootstrap alias delegates to initialize."""
    service = BootstrapService(project_root=tmp_path)
    result = service.bootstrap()
    assert result.state == BootstrapState.RUNNING
    service.shutdown()


def test_initialize_while_initialising_raises() -> None:
    """Bootstrap rejects duplicate initialization while startup is in progress."""
    configuration = FakeConfigurationService()
    logging = FakeLoggingService(configuration)
    service = BootstrapService(configuration, logging)  # type: ignore[arg-type]
    service._state = BootstrapState.INITIALISING

    with pytest.raises(BootstrapStateError):
        service.initialize()
