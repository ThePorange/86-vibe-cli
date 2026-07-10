"""Deterministic JSON serialization for CLI output."""

from __future__ import annotations

import enum
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

from vibe.cli.errors import CLIOutputError


def serialize_value(value: object) -> object:
    """Serialize a supported value for JSON output."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in sorted(value.items(), key=str)}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return serialize_value(asdict(value))
    raise CLIOutputError(f"Unsupported value type for JSON output: {type(value).__name__}")


def dumps_json(value: object) -> str:
    """Serialize a value to deterministic JSON text."""
    serialized = serialize_value(value)
    return json.dumps(serialized, indent=2, sort_keys=True) + "\n"
