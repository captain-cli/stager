from __future__ import annotations

import os
from pathlib import Path

from captain_core.errors import ManifestError
from captain_core.manifests import load_tool_manifest
from captain_core.models import ManifestHeader
from captain_core.project_manifest import load_captain_manifest, resolve_tool_config

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
    """Load a legacy standalone Stager manifest.

    Captain-owned project manifests use ``load_project_manifest`` instead.
    This path remains available for direct Stager compatibility.
    """
    resolved = load_tool_manifest(
        reference,
        tool="stager",
    )

    return parse_manifest_document(
        resolved.document,
        header=resolved.header,
        source_path=resolved.path,
    )


def load_project_manifest(project_root: str | Path | None = None) -> Manifest:
    """Resolve Stager configuration owned by a Captain project."""
    captain_manifest = load_captain_manifest(start=project_root)
    resolved = resolve_tool_config(
        "stager",
        start=captain_manifest.path.parent,
        required=True,
    )
    assert resolved is not None

    project = captain_manifest.document["project"]
    header = ManifestHeader(
        id=project["name"],
        name=project["name"],
        tool="stager",
        category="filesystems",
        schema_version="captain/manifest/v1",
        manifest_version=project["version"],
    )

    # Captain project-relative Stager sources are anchored at the project root
    # for both inline and split configuration. The physical split-manifest
    # location is an implementation detail of Captain's manifest system.
    return parse_manifest_document(
        resolved.config,
        header=header,
        source_path=captain_manifest.path,
    )


def load_manifest(reference: str | None, project_root: str | Path | None) -> Manifest:
    if reference is not None and project_root is not None:
        raise ManifestError("Specify either a Stager manifest or --project, not both.")
    if project_root is not None:
        return load_project_manifest(project_root)
    if reference is None:
        raise ManifestError("A Stager manifest or --project is required.")
    return load_resolved_manifest(reference)


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


def validate(reference: str | None = None, *, project_root: str | Path | None = None) -> Manifest:
    return load_manifest(reference, project_root)


def plan(
    reference: str | None = None,
    root_override: str | None = None,
    target_name: str | None = None,
    source_root_override: str | None = None,
    *,
    project_root: str | Path | None = None,
):
    manifest = load_manifest(reference, project_root)

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
    reference: str | None = None,
    *,
    project_root: str | Path | None = None,
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
        project_root=project_root,
    )

    return execute_plan(
        manifest.id,
        root,
        operations,
        dry_run=dry_run,
        force=force,
    )
