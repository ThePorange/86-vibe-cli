"""Version metadata tests."""

from __future__ import annotations

import json
import sys

from vibe.cli.version import get_version_info


def test_version_info_contains_required_fields() -> None:
    """Version metadata includes required fields."""
    info = get_version_info()
    assert info.platform == "86-vibe"
    assert info.cli_version
    assert info.architecture_version
    assert info.python_version == sys.version.split()[0]
    assert info.build == "development"


def test_version_json_is_deterministic() -> None:
    """Version JSON uses stable key ordering."""
    payload = get_version_info().as_dict()
    encoded = json.dumps(payload, sort_keys=True)
    assert encoded.index("architecture_version") < encoded.index("build")
    assert encoded.index("cli_version") < encoded.index("platform")
