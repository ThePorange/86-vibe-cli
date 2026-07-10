"""Architecture document discovery."""

from __future__ import annotations

import re
from pathlib import Path

from vibe.repository.models import ArchitectureDocument

_DOCUMENT_ID_PATTERN = re.compile(r"^\|\s*\*?\*?Document ID\*?\*?\s*\|\s*(.+?)\s*\|", re.I)
_DOCUMENT_NAME_PATTERN = re.compile(
    r"^\|\s*\*?\*?(?:Document Name|Title)\*?\*?\s*\|\s*(.+?)\s*\|",
    re.I,
)
_PACKAGE_PATTERN = re.compile(
    r"^\|\s*\*?\*?(?:Package|Architecture Package)\*?\*?\s*\|\s*(.+?)\s*\|",
    re.I,
)
_STATUS_PATTERN = re.compile(r"^\|\s*\*?\*?Status\*?\*?\s*\|\s*(.+?)\s*\|", re.I)
_HEADING_PATTERN = re.compile(r"^#\s+(.+)$")


def discover_architecture_documents(root: Path) -> tuple[ArchitectureDocument, ...]:
    """Discover architecture documents under approved locations."""
    documents: list[ArchitectureDocument] = []
    for base in _architecture_locations(root):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            documents.append(_extract_document_metadata(path, relative))
    documents.sort(key=lambda item: item.path)
    return tuple(documents)


def _architecture_locations(root: Path) -> tuple[Path, ...]:
    return (
        root / "architecture",
        root / "docs" / "architecture",
    )


def _extract_document_metadata(path: Path, relative: str) -> ArchitectureDocument:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ArchitectureDocument(
            document_id=None,
            title=None,
            package=None,
            status=None,
            path=relative,
            complete=False,
        )

    document_id = None
    title = None
    package = None
    status = None
    for line in text.splitlines()[:40]:
        if document_id is None:
            match = _DOCUMENT_ID_PATTERN.match(line.strip())
            if match:
                document_id = match.group(1).strip()
        if title is None:
            match = _DOCUMENT_NAME_PATTERN.match(line.strip())
            if match:
                title = match.group(1).strip()
        if package is None:
            match = _PACKAGE_PATTERN.match(line.strip())
            if match:
                package = match.group(1).strip()
        if status is None:
            match = _STATUS_PATTERN.match(line.strip())
            if match:
                status = match.group(1).strip()

    if title is None:
        for line in text.splitlines():
            match = _HEADING_PATTERN.match(line.strip())
            if match:
                title = match.group(1).strip()
                break

    complete = all(value is not None for value in (document_id, title, package, status))
    return ArchitectureDocument(
        document_id=document_id,
        title=title,
        package=package,
        status=status,
        path=relative,
        complete=complete,
    )
