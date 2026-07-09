"""Secret redaction utilities."""

from __future__ import annotations

import re
from typing import Any

REDACTED_VALUE = "********"

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passwd|pwd|secret|token|api[_-]?key|apikey|authorization|auth|"
    r"private[_-]?key|certificate|credential)",
    re.IGNORECASE,
)


def is_sensitive_key(key: str) -> bool:
    """Return whether a field name is considered sensitive."""
    return _SENSITIVE_KEY_PATTERN.search(key) is not None


def redact_value(key: str, value: Any) -> Any:
    """Redact a value when its key is sensitive."""
    if is_sensitive_key(key):
        return REDACTED_VALUE
    return sanitize_value(value)


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize structured values for logging."""
    if isinstance(value, dict):
        return sanitize_mapping(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_value(item) for item in value)
    try:
        return str(value)
    except Exception:
        return repr(value)


def sanitize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a mapping by redacting sensitive keys recursively."""
    sanitized: dict[str, Any] = {}
    for key, value in mapping.items():
        if is_sensitive_key(key):
            sanitized[key] = REDACTED_VALUE
        elif isinstance(value, dict):
            sanitized[key] = sanitize_mapping(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_mapping(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_value(item) for item in value]
        else:
            sanitized[key] = sanitize_value(value)
    return sanitized


def redact_message(message: str) -> str:
    """Apply conservative pattern-based redaction to free-form messages."""
    patterns = (
        (re.compile(r"(?i)(authorization:\s*)(\S+)"), r"\1********"),
        (re.compile(r"(?i)(bearer\s+)(\S+)"), r"\1********"),
        (re.compile(r"(?i)(api[_-]?key=)(\S+)"), r"\1********"),
    )
    redacted = message
    for pattern, replacement in patterns:
        redacted = pattern.sub(replacement, redacted)
    return redacted
