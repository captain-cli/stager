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


def resolve_source_root(
    manifest: Manifest,
    source_root_override: str | None,
) -> Path:
    configured_root = (
        source_root_override
        or os.environ.get("STAGER_SOURCE_ROOT")
        or manifest.source_root
    )

    if configured_root:
        configured_path = Path(configured_root).expanduser()

        if configured_path.is_absolute():
            return configured_path.resolve()

        return (
            manifest.source_path.parent
            / configured_path
        ).resolve()

    return manifest.source_path.parent.resolve()


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


def select_target(
    manifest: Manifest,
    target_name: str | None,
) -> Manifest:
    if target_name is None:
        return manifest

    target = manifest.targets.get(target_name)

    if target is None:
        available = ", ".join(sorted(manifest.targets))

        if available:
            raise ManifestError(
                f'Unknown target "{target_name}". '
                f"Available targets: {available}."
            )

        raise ManifestError(
            f'Unknown target "{target_name}". '
            "Manifest defines no targets."
        )

    return Manifest(
        manifest.id,
        manifest.name,
        manifest.version,
        target.default_root,
        target.variables,
        target.directories,
        target.files,
        target.copies,
        {},
        manifest.source_path,
        target.source_root,
    )


def validate(reference: str) -> Manifest:
    return load_resolved_manifest(reference)


def plan(
    reference: str,
    root_override: str | None = None,
    target_name: str | None = None,
    source_root_override: str | None = None,
):
    manifest = load_resolved_manifest(reference)

    manifest = select_target(
        manifest,
        target_name,
    )

    root = resolve_root(
        manifest,
        root_override,
    )

    source_root = resolve_source_root(
        manifest,
        source_root_override,
    )

    operations = build_plan(
        manifest,
        root,
        source_root,
    )

    return manifest, root, operations


def apply(
    reference: str,
    *,
    root_override: str | None = None,
    target_name: str | None = None,
    source_root_override: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> ExecutionReport:
    manifest, root, operations = plan(
        reference,
        root_override,
        target_name,
        source_root_override,
    )

    return execute_plan(
        manifest.id,
        root,
        operations,
        dry_run=dry_run,
        force=force,
    )
