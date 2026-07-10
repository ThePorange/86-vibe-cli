"""Bootstrap Service orchestration and public API."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path

from vibe.bootstrap.exceptions import (
    BootstrapInitializationError,
    BootstrapShutdownError,
    BootstrapStateError,
)
from vibe.bootstrap.models import BootstrapResult
from vibe.bootstrap.state import BootstrapState, transition
from vibe.configuration.exceptions import ConfigurationError
from vibe.configuration.service import ConfigurationService
from vibe.logging.exceptions import LoggingServiceError
from vibe.logging.service import LoggingService
from vibe.registry import (
    SERVICE_NAME_BOOTSTRAP,
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_SERVICE_REGISTRY,
)
from vibe.registry.metadata import ServiceMetadata
from vibe.registry.service import ServiceRegistry
from vibe.version import PLATFORM_VERSION


class BootstrapService:
    """Coordinates deterministic platform startup and shutdown."""

    def __init__(
        self,
        configuration_service: ConfigurationService | None = None,
        logging_service: LoggingService | None = None,
        service_registry: ServiceRegistry | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the bootstrap service.

        Args:
            configuration_service:
                Optional configuration service instance for dependency injection.
            logging_service:
                Optional logging service instance for dependency injection.
            service_registry:
                Optional service registry instance for dependency injection.
            project_root:
                Optional project root used for service discovery.
        """
        self._project_root = project_root or Path.cwd()
        self._service_registry = service_registry or ServiceRegistry()
        self._configuration_service = configuration_service or ConfigurationService(
            project_root=self._project_root
        )
        self._logging_service = logging_service or LoggingService(
            self._configuration_service,
            project_root=self._project_root,
        )
        self._state = BootstrapState.NOT_STARTED
        self._result: BootstrapResult | None = None
        self._lock = threading.RLock()

    def initialize(self) -> BootstrapResult:
        """Execute the platform bootstrap sequence.

        Returns:
            Immutable bootstrap result describing the running platform.

        Raises:
            BootstrapStateError:
                When initialization is requested from an invalid state.
            BootstrapInitializationError:
                When startup fails.
        """
        with self._lock:
            if self._state == BootstrapState.RUNNING:
                if self._result is None:
                    raise BootstrapStateError("Bootstrap is running without a bootstrap result.")
                return self._result

            if self._state == BootstrapState.INITIALISING:
                raise BootstrapStateError("Bootstrap initialization is already in progress.")

            if self._state == BootstrapState.FAILED:
                raise BootstrapStateError(
                    "Bootstrap initialization cannot be retried after failure."
                )

            if self._state != BootstrapState.NOT_STARTED:
                raise BootstrapStateError(
                    f"Bootstrap cannot initialize from state {self._state.value}."
                )

            self._state = transition(self._state, BootstrapState.INITIALISING)
            logging_available = False

            try:
                self._initialize_configuration_service()
                self._initialize_logging_service()
                logging_available = True
                self._service_registry.set_logger(self._logging_service.get_logger("registry"))
                self._register_platform_services()
                self._emit_startup_diagnostics()
                started_at = datetime.now(UTC)
                self._result = BootstrapResult(
                    state=BootstrapState.RUNNING,
                    started_at=started_at,
                    configuration_service=self._configuration_service,
                    logging_service=self._logging_service,
                    service_registry=self._service_registry,
                )
                self._state = transition(self._state, BootstrapState.RUNNING)
                return self._result
            except Exception as exc:
                self._state = transition(self._state, BootstrapState.FAILED)
                if logging_available:
                    logger = self._logging_service.get_logger("bootstrap")
                    logger.error("Bootstrap initialization failed", error_type=type(exc).__name__)
                    self._safe_shutdown_after_failure()
                message = "Bootstrap initialization failed."
                if isinstance(exc, BootstrapInitializationError):
                    raise
                if isinstance(exc, (ConfigurationError, LoggingServiceError)):
                    raise BootstrapInitializationError(message) from exc
                raise BootstrapInitializationError(message) from exc

    def bootstrap(self) -> BootstrapResult:
        """Execute the platform bootstrap sequence.

        Returns:
            Immutable bootstrap result describing the running platform.
        """
        return self.initialize()

    def shutdown(self) -> None:
        """Shut down initialized services in reverse dependency order.

        Raises:
            BootstrapStateError:
                When shutdown is requested while another shutdown is in progress.
            BootstrapShutdownError:
                When one or more shutdown operations fail.
        """
        with self._lock:
            if self._state in {BootstrapState.NOT_STARTED, BootstrapState.STOPPED}:
                return

            if self._state == BootstrapState.SHUTTING_DOWN:
                raise BootstrapStateError("Bootstrap shutdown is already in progress.")

            if self._state == BootstrapState.INITIALISING:
                raise BootstrapStateError("Bootstrap cannot shut down while initializing.")

            previous_state = self._state
            self._state = transition(self._state, BootstrapState.SHUTTING_DOWN)
            shutdown_errors: list[Exception] = []
            logger = None

            if self._logging_service.is_initialized:
                logger = self._logging_service.get_logger("bootstrap")
                logger.info("Bootstrap shutdown initiated")

            if self._logging_service.is_initialized:
                try:
                    self._logging_service.shutdown()
                    if logger is not None:
                        logger.info("Logging service shutdown complete")
                except Exception as exc:
                    shutdown_errors.append(exc)
                    if logger is not None:
                        logger.error(
                            "Logging service shutdown failed",
                            error_type=type(exc).__name__,
                        )

            if self._configuration_service.is_initialized:
                try:
                    self._configuration_service.shutdown()
                    if logger is not None:
                        logger.info("Configuration service shutdown complete")
                except Exception as exc:
                    shutdown_errors.append(exc)
                    if logger is not None:
                        logger.error(
                            "Configuration service shutdown failed",
                            error_type=type(exc).__name__,
                        )

            self._result = None
            if shutdown_errors:
                self._state = transition(self._state, BootstrapState.FAILED)
                raise BootstrapShutdownError("Bootstrap shutdown failed.") from shutdown_errors[0]

            self._state = transition(self._state, BootstrapState.STOPPED)
            if logger is not None:
                logger.info("Bootstrap shutdown complete")
            elif previous_state == BootstrapState.FAILED:
                pass

    @property
    def state(self) -> BootstrapState:
        """Return the current bootstrap state."""
        with self._lock:
            return self._state

    def status(self) -> BootstrapState:
        """Return the current bootstrap state."""
        return self.state

    @property
    def is_running(self) -> bool:
        """Return whether the platform has completed bootstrap."""
        with self._lock:
            return self._state == BootstrapState.RUNNING

    def is_ready(self) -> bool:
        """Return whether the platform has completed bootstrap."""
        return self.is_running

    @property
    def result(self) -> BootstrapResult:
        """Return the bootstrap result for a running platform.

        Raises:
            BootstrapStateError:
                When bootstrap has not completed successfully.
        """
        with self._lock:
            if self._state != BootstrapState.RUNNING or self._result is None:
                raise BootstrapStateError("Bootstrap result is unavailable before startup.")
            return self._result

    @property
    def configuration_service(self) -> ConfigurationService:
        """Return the managed configuration service.

        Raises:
            BootstrapStateError:
                When accessed before bootstrap has reached the running state.
        """
        self._require_running("Configuration Service")
        return self._configuration_service

    @property
    def logging_service(self) -> LoggingService:
        """Return the managed logging service.

        Raises:
            BootstrapStateError:
                When accessed before bootstrap has reached the running state.
        """
        self._require_running("Logging Service")
        return self._logging_service

    @property
    def service_registry(self) -> ServiceRegistry:
        """Return the managed service registry.

        Raises:
            BootstrapStateError:
                When accessed before bootstrap has reached the running state.
        """
        self._require_running("Service Registry")
        return self._service_registry

    def _require_running(self, service_name: str) -> None:
        with self._lock:
            if self._state != BootstrapState.RUNNING:
                raise BootstrapStateError(
                    f"{service_name} is unavailable before bootstrap completes."
                )

    def _initialize_configuration_service(self) -> None:
        try:
            if not self._configuration_service.is_initialized:
                self._configuration_service.initialize()
            self._configuration_service.load()
            if not self._configuration_service.validate():
                raise BootstrapInitializationError("Configuration validation failed.")
        except BootstrapInitializationError:
            raise
        except Exception as exc:
            raise BootstrapInitializationError(
                "Failed to initialize Configuration Service."
            ) from exc

    def _initialize_logging_service(self) -> None:
        try:
            if not self._logging_service.is_initialized:
                self._logging_service.initialize()
        except Exception as exc:
            raise BootstrapInitializationError("Failed to initialize Logging Service.") from exc

    def _register_platform_services(self) -> None:
        registry = self._service_registry
        registry.register(
            SERVICE_NAME_SERVICE_REGISTRY,
            registry,
            ServiceMetadata(
                name=SERVICE_NAME_SERVICE_REGISTRY,
                service_type="ServiceRegistry",
                package="vibe.registry",
                version=PLATFORM_VERSION,
                description="Platform service registry",
            ),
        )
        registry.register(
            SERVICE_NAME_BOOTSTRAP,
            self,
            ServiceMetadata(
                name=SERVICE_NAME_BOOTSTRAP,
                service_type="BootstrapService",
                package="vibe.bootstrap",
                version=PLATFORM_VERSION,
                description="Platform bootstrap orchestration",
                dependencies=(SERVICE_NAME_CONFIGURATION, SERVICE_NAME_LOGGING),
            ),
        )
        registry.register(
            SERVICE_NAME_CONFIGURATION,
            self._configuration_service,
            ServiceMetadata(
                name=SERVICE_NAME_CONFIGURATION,
                service_type="ConfigurationService",
                package="vibe.configuration",
                version=PLATFORM_VERSION,
                description="Platform configuration access",
            ),
        )
        registry.register(
            SERVICE_NAME_LOGGING,
            self._logging_service,
            ServiceMetadata(
                name=SERVICE_NAME_LOGGING,
                service_type="LoggingService",
                package="vibe.logging",
                version=PLATFORM_VERSION,
                description="Platform logging",
                dependencies=(SERVICE_NAME_CONFIGURATION,),
            ),
        )

    def _emit_startup_diagnostics(self) -> None:
        logger = self._logging_service.get_logger("bootstrap")
        logger.info("Bootstrap startup initiated")
        logger.info("Configuration service initialized")
        logger.info("Logging service initialized")
        logger.info("Platform services registered")
        logger.info("Platform running")

    def _safe_shutdown_after_failure(self) -> None:
        try:
            if self._logging_service.is_initialized:
                self._logging_service.shutdown()
        except Exception:
            pass
        try:
            if self._configuration_service.is_initialized:
                self._configuration_service.shutdown()
        except Exception:
            pass
