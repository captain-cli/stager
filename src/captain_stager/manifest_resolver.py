from __future__ import annotations

from pathlib import Path

from .errors import ManifestError
from .project import resolve_captain_root


STAGER_MANIFEST_ROOT = Path("manifests") / "stager"


def resolve_manifest_reference(
    reference: str,
    *,
    project_root: Path | None = None,
) -> Path:
    """
    Resolve either:

    - An explicit JSON path
    - A Stager manifest reference such as:
      filesystems/omni-shell-demo
    """

    supplied_path = Path(reference).expanduser()

    # Explicit absolute or relative file path.
    if supplied_path.is_file():
        return supplied_path.resolve()

    if supplied_path.suffix == ".json":
        explicit_candidate = (Path.cwd() / supplied_path).resolve()

        if explicit_candidate.is_file():
            return explicit_candidate

    captain_root = resolve_captain_root(project_root)
    manifest_root = captain_root / STAGER_MANIFEST_ROOT

    normalized_reference = reference.replace("\\", "/").strip("/")

    if not normalized_reference:
        raise ManifestError("Manifest reference cannot be empty.")

    reference_path = Path(normalized_reference)

    if ".." in reference_path.parts:
        raise ManifestError(
            f"Manifest reference cannot escape its root: {reference}"
        )

    if reference_path.suffix != ".json":
        reference_path = reference_path.with_suffix(".json")

    candidate = (manifest_root / reference_path).resolve()
    resolved_manifest_root = manifest_root.resolve()

    if (
        candidate != resolved_manifest_root
        and resolved_manifest_root not in candidate.parents
    ):
        raise ManifestError(
            f"Manifest reference escapes Stager manifest root: {reference}"
        )

    if candidate.is_file():
        return candidate

    raise ManifestError(
        f"Unable to locate Stager manifest: {reference}\n"
        f"Searched: {candidate}"
    )
