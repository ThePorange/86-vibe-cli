"""Bootstrap result model unit tests."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from vibe.bootstrap.service import BootstrapService
from vibe.bootstrap.state import BootstrapState


def test_bootstrap_result_is_immutable(tmp_path: Path) -> None:
    """Bootstrap result exposes only implemented services and UTC timestamps."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()
    assert result.state == BootstrapState.RUNNING
    assert result.started_at.tzinfo is UTC
    assert result.configuration_service is service.configuration_service
    assert result.logging_service is service.logging_service
    assert result.service_registry is service.service_registry
    assert result.lifecycle_manager is service.lifecycle_manager
    service.shutdown()

    with pytest.raises(AttributeError):
        result.state = BootstrapState.STOPPED  # type: ignore[misc]
