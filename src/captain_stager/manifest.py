from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ManifestError
from .models import FileSpec, Manifest
from .paths import validate_relative_path
from .variables import substitute


def load_manifest_document(
    data: dict[str, Any],
    *,
    source_path: Path,
) -> Manifest:
    header = data.get("header")

    if not isinstance(header, dict):
        raise ManifestError(
            'Manifest property "header" must be an object.'
        )

    manifest_id = header["id"]
    name = header["name"]
    version = header["manifestVersion"]

    default_root = data.get("defaultRoot")

    if default_root is not None and (
        not isinstance(default_root, str)
        or not default_root.strip()
    ):
        raise ManifestError(
            '"defaultRoot" must be a non-empty string when provided.'
        )

    raw_variables = data.get("variables", {})

    if not isinstance(raw_variables, dict):
        raise ManifestError('"variables" must be an object.')

    variables: dict[str, str] = {}

    for key, value in raw_variables.items():
        if not isinstance(key, str) or not key:
            raise ManifestError(
                "Variable names must be non-empty strings."
            )

        if not isinstance(value, (str, int, float, bool)):
            raise ManifestError(
                f"Variable {key} must be scalar."
            )

        variables[key] = str(value)

    raw_directories = data.get("directories", [])

    if not isinstance(raw_directories, list):
        raise ManifestError('"directories" must be an array.')

    directories: list[str] = []

    for index, value in enumerate(raw_directories):
        if not isinstance(value, str):
            raise ManifestError(
                f"directories[{index}] must be a string."
            )

        substituted = substitute(
            value,
            variables,
            f"directories[{index}]",
        )

        directories.append(
            validate_relative_path(
                substituted,
                f"directories[{index}]",
            )
        )

    raw_files = data.get("files", [])

    if not isinstance(raw_files, list):
        raise ManifestError('"files" must be an array.')

    files: list[FileSpec] = []

    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise ManifestError(
                f"files[{index}] must be an object."
            )

        raw_path = item.get("path")

        if not isinstance(raw_path, str):
            raise ManifestError(
                f"files[{index}].path must be a string."
            )

        file_path = validate_relative_path(
            substitute(
                raw_path,
                variables,
                f"files[{index}].path",
            ),
            f"files[{index}].path",
        )

        content = item.get("content", "")
        encoding = item.get("encoding", "utf-8")
        overwrite = item.get("overwrite", False)

        if not isinstance(content, str):
            raise ManifestError(
                f"files[{index}].content must be a string."
            )

        if not isinstance(encoding, str) or not encoding:
            raise ManifestError(
                f"files[{index}].encoding must be a string."
            )

        if not isinstance(overwrite, bool):
            raise ManifestError(
                f"files[{index}].overwrite must be boolean."
            )

        files.append(
            FileSpec(
                file_path,
                substitute(
                    content,
                    variables,
                    f"files[{index}].content",
                ),
                encoding,
                overwrite,
            )
        )

    return Manifest(
        manifest_id,
        name,
        version,
        default_root.strip()
        if isinstance(default_root, str)
        else None,
        variables,
        tuple(dict.fromkeys(directories)),
        tuple(files),
        source_path,
    )