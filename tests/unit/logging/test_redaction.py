"""Redaction unit tests."""

from __future__ import annotations

from vibe.logging.redaction import (
    REDACTED_VALUE,
    is_sensitive_key,
    redact_message,
    redact_value,
    sanitize_mapping,
)


def test_is_sensitive_key_matches_required_patterns() -> None:
    """Sensitive key patterns are detected case-insensitively."""
    assert is_sensitive_key("api_key")
    assert is_sensitive_key("Authorization")
    assert is_sensitive_key("user_password")
    assert is_sensitive_key("credential_id")


def test_redact_value_masks_sensitive_keys() -> None:
    """Sensitive values are masked."""
    assert redact_value("api_key", "secret-value") == REDACTED_VALUE
    assert redact_value("provider", "openrouter") == "openrouter"


def test_sanitize_mapping_redacts_nested_metadata() -> None:
    """Nested structured metadata is redacted recursively."""
    sanitized = sanitize_mapping(
        {
            "provider": "openrouter",
            "connection": {"api_key": "secret-value", "region": "us-east-1"},
        }
    )
    assert sanitized["provider"] == "openrouter"
    assert sanitized["connection"]["api_key"] == REDACTED_VALUE
    assert sanitized["connection"]["region"] == "us-east-1"
    assert "secret-value" not in str(sanitized)


def test_redact_message_masks_inline_authorization() -> None:
    """Inline authorization values are masked in free-form messages."""
    message = redact_message("Authorization: bearer-token-value")
    assert "bearer-token-value" not in message
    assert REDACTED_VALUE in message
