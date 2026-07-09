"""Handler unit tests."""

from __future__ import annotations

import logging
from pathlib import Path

from vibe.logging.handlers import (
    DEBUG_LOG_FILE,
    ERROR_LOG_FILE,
    PLATFORM_LOG_FILE,
    create_handlers,
    ensure_log_directory,
    log_directory,
)


def test_ensure_log_directory_creates_project_log_directory(tmp_path: Path) -> None:
    """Log directory is created under the project metadata directory."""
    directory = ensure_log_directory(tmp_path)
    assert directory == log_directory(tmp_path)
    assert directory.is_dir()


def test_create_handlers_writes_expected_log_files(tmp_path: Path) -> None:
    """Enabled handlers create platform, error, and debug log files."""
    handler_set = create_handlers(
        project_root=tmp_path,
        console_enabled=False,
        file_enabled=True,
        debug_enabled=True,
        rotation_enabled=True,
        colored_console=False,
        console_level="INFO",
        file_level="DEBUG",
        max_bytes=128,
        backup_count=2,
    )
    logger = logging.getLogger("vibe.handlers.test")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in handler_set.handlers:
        logger.addHandler(handler)

    logger.info("platform info event")
    logger.error("platform error event")
    logger.debug("platform debug event")
    for handler in handler_set.handlers:
        handler.flush()

    log_dir = log_directory(tmp_path)
    assert (log_dir / PLATFORM_LOG_FILE).exists()
    assert (log_dir / ERROR_LOG_FILE).exists()
    assert (log_dir / DEBUG_LOG_FILE).exists()
    handler_set.close()


def test_create_handlers_respects_disabled_outputs(tmp_path: Path) -> None:
    """Disabled console and file outputs do not create handlers."""
    handler_set = create_handlers(
        project_root=tmp_path,
        console_enabled=False,
        file_enabled=False,
        debug_enabled=False,
        rotation_enabled=False,
        colored_console=False,
        console_level="INFO",
        file_level="DEBUG",
    )
    assert handler_set.handlers == []
