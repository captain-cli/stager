from __future__ import annotations

import os
from pathlib import Path

from captain_core.errors import ManifestError
from captain_core.manifests import load_tool_manifest

from .executor import execute_plan
from .manifest import parse_manifest_document
from .models import ExecutionReport, Manifest
from .planner import build_plan


def resolve_root(
    manifest: Manifest,
    root_override: str | None,
) -> Path:
    configured_root = (
        root_override
        or os.environ.get("STAGER_ROOT")
        or manifest.default_root
    )

    if not configured_root:
        raise ManifestError(
            "No target root configured. Use --root, "
            "STAGER_ROOT, or manifest.defaultRoot."
        )

    return Path(configured_root).expanduser().resolve()


def load_resolved_manifest(reference: str) -> Manifest:
    resolved = load_tool_manifest(
        reference,
        tool="stager",
    )

    return parse_manifest_document(
        resolved.document,
        header=resolved.header,
        source_path=resolved.path,
    )


def validate(reference: str) -> Manifest:
    return load_resolved_manifest(reference)


def plan(
    reference: str,
    root_override: str | None = None,
):
    manifest = load_resolved_manifest(reference)
    root = resolve_root(manifest, root_override)
    operations = build_plan(manifest, root)

    return manifest, root, operations


def apply(
    reference: str,
    *,
    root_override: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> ExecutionReport:
    manifest, root, operations = plan(
        reference,
        root_override,
    )

    return execute_plan(
        manifest.id,
        root,
        operations,
        dry_run=dry_run,
        force=force,
    )
