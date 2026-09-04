from __future__ import annotations

from pathlib import Path
from typing import Any

from captain_core.errors import ManifestError
from captain_core.models import ManifestHeader
from .paths import validate_relative_path
from .variables import substitute
from .models import CopySpec, FileSpec, Manifest, TargetSpec

def parse_mode(value) -> int | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ManifestError(
            'mode must be a string such as "0755".'
        )

    try:
        mode = int(value, 8)
    except ValueError as exc:
        raise ManifestError(
            f'Invalid file mode "{value}".'
        ) from exc

    if mode < 0 or mode > 0o7777:
        raise ManifestError(
            f'Invalid file mode "{value}".'
        )

    return mode

def parse_manifest_document(
    data: dict[str, Any],
    *,
    header: ManifestHeader,
    source_path: Path,
) -> Manifest:

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
                parse_mode(item.get("mode"))
            )
        )

    raw_copies = data.get("copies", [])

    if not isinstance(raw_copies, list):
        raise ManifestError('"copies" must be an array.')

    copies: list[CopySpec] = []

    for index, item in enumerate(raw_copies):
        if not isinstance(item, dict):
            raise ManifestError(
                f"copies[{index}] must be an object."
            )

        source = item.get("source")
        path = item.get("path")
        overwrite = item.get("overwrite", False)

        if not isinstance(source, str) or not source.strip():
            raise ManifestError(
                f"copies[{index}].source must be a string."
            )

        if not isinstance(path, str) or not path.strip():
            raise ManifestError(
                f"copies[{index}].path must be a string."
            )

        if not isinstance(overwrite, bool):
            raise ManifestError(
                f"copies[{index}].overwrite must be boolean."
            )

        copies.append(
            CopySpec(
                source=source.strip(),
                path=path.strip(),
                overwrite=overwrite,
                mode=parse_mode(item.get("mode")),
            )
        )


    raw_targets = data.get("targets", {})

    if not isinstance(raw_targets, dict):
        raise ManifestError('"targets" must be an object.')

    targets: dict[str, TargetSpec] = {}

    for target_name, target_data in raw_targets.items():
        if not isinstance(target_name, str) or not target_name.strip():
            raise ManifestError(
            "Target names must be non-empty strings."
            )

        if not isinstance(target_data, dict):
            raise ManifestError(
                f'targets["{target_name}"] must be an object.'
            )

        target_root = target_data.get("defaultRoot")

        if target_root is not None and (
            not isinstance(target_root, str)
            or not target_root.strip()
        ):
            raise ManifestError(
                f'targets["{target_name}"].defaultRoot '
                "must be a non-empty string when provided."
            )


        raw_target_variables = target_data.get(
            "variables",
            {},
        )

        if not isinstance(
                raw_target_variables,
                dict,
        ):
            raise ManifestError(
                f'targets["{target_name}"].variables '
                "must be an object."
            )

        target_variables: dict[str, str] = {}

        for key, value in raw_target_variables.items():
            if not isinstance(key, str) or not key:
                raise ManifestError(
                    f'targets["{target_name}"] variable names '
                    "must be non-empty strings."
                )

            if not isinstance(
                    value,
                    (str, int, float, bool),
            ):
                raise ManifestError(
                    f'targets["{target_name}"].variables["{key}"] '
                    "must be scalar."
                )

            target_variables[key] = str(value)

        raw_target_directories = target_data.get(
            "directories",
            [],
        )

        if not isinstance(
                raw_target_directories,
                list,
        ):
            raise ManifestError(
                f'targets["{target_name}"].directories '
                "must be an array."
            )

        target_directories: list[str] = []

        for index, value in enumerate(
                raw_target_directories
        ):
            if not isinstance(value, str):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'directories[{index}] must be a string.'
                )

            substituted = substitute(
                value,
                target_variables,
                f'targets["{target_name}"].'
                f'directories[{index}]',
            )

            target_directories.append(
                validate_relative_path(
                    substituted,
                    f'targets["{target_name}"].'
                    f'directories[{index}]',
                )
            )

        raw_target_files = target_data.get(
            "files",
            [],
        )

        if not isinstance(raw_target_files, list):
            raise ManifestError(
                f'targets["{target_name}"].files '
                "must be an array."
            )

        target_files: list[FileSpec] = []

        for index, item in enumerate(raw_target_files):
            if not isinstance(item, dict):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'files[{index}] must be an object.'
                )

            raw_path = item.get("path")

            if not isinstance(raw_path, str):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'files[{index}].path must be a string.'
                )

            file_path = validate_relative_path(
                substitute(
                    raw_path,
                    target_variables,
                    f'targets["{target_name}"].'
                    f'files[{index}].path',
                ),
                f'targets["{target_name}"].'
                f'files[{index}].path',
            )

            content = item.get("content", "")
            encoding = item.get("encoding", "utf-8")
            overwrite = item.get("overwrite", False)

            if not isinstance(content, str):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'files[{index}].content must be a string.'
                )

            if not isinstance(encoding, str) or not encoding:
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'files[{index}].encoding must be a string.'
                )

            if not isinstance(overwrite, bool):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'files[{index}].overwrite must be boolean.'
                )

            target_files.append(
                FileSpec(
                    file_path,
                    substitute(
                        content,
                        target_variables,
                        f'targets["{target_name}"].'
                        f'files[{index}].content',
                    ),
                    encoding,
                    overwrite,
                    parse_mode(item.get("mode"))
                )
            )

        raw_target_copies = target_data.get(
            "copies",
            [],
        )

        if not isinstance(raw_target_copies, list):
            raise ManifestError(
                f'targets["{target_name}"].copies '
                "must be an array."
            )

        target_copies: list[CopySpec] = []

        for index, item in enumerate(raw_target_copies):
            if not isinstance(item, dict):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'copies[{index}] must be an object.'
                )

            source = item.get("source")
            path = item.get("path")
            overwrite = item.get("overwrite", False)

            if not isinstance(source, str) or not source.strip():
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'copies[{index}].source must be a string.'
                )

            if not isinstance(path, str) or not path.strip():
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'copies[{index}].path must be a string.'
                )

            if not isinstance(overwrite, bool):
                raise ManifestError(
                    f'targets["{target_name}"].'
                    f'copies[{index}].overwrite must be boolean.'
                )

            target_copies.append(
                CopySpec(
                    source=source.strip(),
                    path=substitute(
                        path.strip(),
                        target_variables,
                        f'targets["{target_name}"].'
                        f'copies[{index}].path',
                    ),
                    overwrite=overwrite,
                    mode=parse_mode(item.get("mode"))
                )
            )

        targets[target_name.strip()] = TargetSpec(
            default_root=(
                target_root.strip()
                if isinstance(target_root, str)
                else None
            ),
            variables=target_variables,
            directories=tuple(
                dict.fromkeys(target_directories)
            ),
            files=tuple(target_files),
            copies=tuple(target_copies),
        )

    return Manifest(
        header.id,
        header.name,
        header.manifest_version,
        default_root.strip()
        if isinstance(default_root, str)
        else None,
        variables,
        tuple(dict.fromkeys(directories)),
        tuple(files),
        tuple(copies),
        targets,
        source_path,
    )