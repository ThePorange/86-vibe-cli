"""Configuration Service orchestration and public API."""

from __future__ import annotations

import re
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from vibe.configuration.environment import discover_env_overrides
from vibe.configuration.exceptions import (
    ConfigurationKeyError,
    ConfigurationLoadError,
    ConfigurationReloadError,
    ConfigurationValidationError,
)
from vibe.configuration.loader import load_defaults, load_project_configuration
from vibe.configuration.merger import apply_dotted_overrides, merge_configurations
from vibe.configuration.models import EffectiveConfiguration, build_effective_configuration
from vibe.configuration.validator import validate_configuration

_SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|token|password|secret|authorization|credential)",
    re.IGNORECASE,
)


class ConfigurationService:
    """Authoritative configuration access for the 86-vibe platform."""

    def __init__(
        self,
        project_root: Path | None = None,
        *,
        overrides: dict[str, Any] | None = None,
        require_project_config: bool = False,
    ) -> None:
        """Initialize the configuration service.

        Args:
            project_root:
                Optional project root used for configuration discovery.
            overrides:
                Runtime overrides with the highest precedence.
            require_project_config:
                When ``True``, initialization fails if project configuration is missing.
        """
        self._project_root = project_root or Path.cwd()
        self._runtime_overrides = deepcopy(overrides or {})
        self._require_project_config = require_project_config
        self._config: dict[str, Any] | None = None
        self._effective_configuration: EffectiveConfiguration | None = None
        self._initialized = False
        self._lock = threading.RLock()

    def initialize(self) -> None:
        """Prepare the service for configuration loading."""
        with self._lock:
            self._initialized = True

    def load(self) -> None:
        """Load configuration from supported sources."""
        with self._lock:
            self._config = self._build_configuration()
            validate_configuration(self._config)
            self._effective_configuration = build_effective_configuration(self._config)
            self._initialized = True

    def reload(self) -> None:
        """Reload configuration from supported sources.

        Raises:
            ConfigurationReloadError:
                When reload validation fails. The previous configuration remains active.
        """
        with self._lock:
            previous_config = self._config
            previous_effective = self._effective_configuration
            try:
                candidate = self._build_configuration()
                validate_configuration(candidate)
            except (ConfigurationLoadError, ConfigurationValidationError) as exc:
                self._config = previous_config
                self._effective_configuration = previous_effective
                raise ConfigurationReloadError("Configuration reload failed.") from exc

            self._config = candidate
            self._effective_configuration = build_effective_configuration(candidate)
            self._initialized = True

    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a configuration value by dotted key.

        Args:
            key:
                Dotted configuration key.
            default:
                Value returned when the key is not present.

        Returns:
            The resolved configuration value.

        Raises:
            ConfigurationKeyError:
                When the key is required but missing and no default is provided.
        """
        with self._lock:
            if self._config is None:
                if default is not None:
                    return default
                raise ConfigurationKeyError(f"Configuration key not found: {key}")

            current: Any = self._config
            for part in key.split("."):
                if not isinstance(current, dict) or part not in current:
                    if default is not None:
                        return default
                    raise ConfigurationKeyError(f"Configuration key not found: {key}")
                current = current[part]
            return deepcopy(current)

    def contains(self, key: str) -> bool:
        """Return whether a configuration key exists.

        Args:
            key:
                Dotted configuration key.

        Returns:
            True when the key resolves to a value.
        """
        return self.exists(key)

    def exists(self, key: str) -> bool:
        """Return whether a configuration key exists.

        Args:
            key:
                Dotted configuration key.

        Returns:
            True when the key resolves to a value.
        """
        with self._lock:
            if self._config is None:
                return False
            current: Any = self._config
            for part in key.split("."):
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]
            return True

    def get_section(self, section: str) -> dict[str, Any]:
        """Return a configuration section as a read-only mapping.

        Args:
            section:
                Top-level configuration section name.

        Returns:
            A deep copy of the requested section.

        Raises:
            ConfigurationKeyError:
                When the section does not exist.
        """
        with self._lock:
            if self._config is None or section not in self._config:
                raise ConfigurationKeyError(f"Configuration section not found: {section}")
            section_value = self._config[section]
            if not isinstance(section_value, dict):
                raise ConfigurationKeyError(f"Configuration section not found: {section}")
            return deepcopy(section_value)

    def validate(self) -> bool:
        """Validate the loaded configuration.

        Returns:
            True when configuration validation succeeds.
        """
        with self._lock:
            if self._config is None:
                return False
            try:
                validate_configuration(self._config)
            except ConfigurationValidationError:
                return False
            return True

    def export(self, *, mask_secrets: bool = True) -> dict[str, Any]:
        """Export the runtime configuration as structured data.

        Args:
            mask_secrets:
                When ``True``, sensitive values are redacted in the export.

        Returns:
            A read-only snapshot of the runtime configuration.
        """
        with self._lock:
            if self._config is None:
                return {}
            exported = deepcopy(self._config)
            if mask_secrets:
                _mask_secrets(exported)
            return exported

    def shutdown(self) -> None:
        """Release configuration service resources."""
        with self._lock:
            self._config = None
            self._effective_configuration = None
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the service has been initialized."""
        with self._lock:
            return self._initialized

    @property
    def configuration(self) -> EffectiveConfiguration | None:
        """Return the immutable effective configuration snapshot."""
        with self._lock:
            return self._effective_configuration

    def _build_configuration(self) -> dict[str, Any]:
        defaults = load_defaults()
        project_config = load_project_configuration(
            self._project_root,
            required=self._require_project_config,
        )
        env_overrides = discover_env_overrides()
        merged = merge_configurations(defaults, project_config, env_overrides)
        return apply_dotted_overrides(merged, self._runtime_overrides)


def _mask_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SECRET_KEY_PATTERN.search(key):
                value[key] = "********"
            else:
                _mask_secrets(item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list)):
                _mask_secrets(item)
            else:
                value[index] = item
