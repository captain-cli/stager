from __future__ import annotations

import os
from pathlib import Path

from .errors import ManifestError


CAPTAIN_DIRECTORY = "captain"


def find_project_root(start: Path | None = None) -> Path:
    """
    Search upward from the current directory for a project containing
    a Captain directory.
    """
    current = (start or Path.cwd()).expanduser().resolve()

    for candidate in (current, *current.parents):
        captain_directory = candidate / CAPTAIN_DIRECTORY

        if captain_directory.is_dir():
            return candidate

    raise ManifestError(
        f'Unable to locate a "{CAPTAIN_DIRECTORY}" directory '
        f"from {current} or any parent directory."
    )


def resolve_captain_root(
    project_root: Path | None = None,
) -> Path:
    configured_root = os.environ.get("CAPTAIN_ROOT")

    if configured_root:
        captain_root = Path(configured_root).expanduser().resolve()

        if not captain_root.is_dir():
            raise ManifestError(
                f"CAPTAIN_ROOT does not exist: {captain_root}"
            )

        return captain_root

    resolved_project_root = project_root or find_project_root()
    captain_root = resolved_project_root / CAPTAIN_DIRECTORY

    if not captain_root.is_dir():
        raise ManifestError(
            f"Captain directory does not exist: {captain_root}"
        )

    return captain_root
