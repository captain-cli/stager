from __future__ import annotations

from pathlib import Path

from captain_core.filesystem import (
    resolve_inside_root as resolve_core_inside_root,
    validate_relative_reference,
)


def validate_relative_path(value: object, field_name: str) -> str:
    """Validate a Stager resource path through Captain Core safety rules."""
    relative_path = validate_relative_reference(value, field_name)  # type: ignore[arg-type]
    return relative_path.as_posix()


def resolve_inside_root(root: Path, relative_path: str) -> Path:
    """Resolve a validated Stager path inside the configured target root."""
    relative = validate_relative_reference(relative_path, "resource path")
    return resolve_core_inside_root(root, relative)
