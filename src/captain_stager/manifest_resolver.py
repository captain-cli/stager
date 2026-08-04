from __future__ import annotations

from pathlib import Path

from captain_core.errors import ManifestError
from .project import resolve_captain_root

from captain_core.manifests import resolve_manifest

def resolve_manifest_reference(reference, project_root=None):
    return resolve_manifest(
        reference,
        tool="stager",
        start=project_root
    )