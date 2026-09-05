import argparse
import json
import sys

from captain_core.errors import CaptainCoreError

from . import __version__
from .output import emit_json, print_report
from .service import apply, plan, validate


def build_parser():
    parser = argparse.ArgumentParser(
        prog="stager",
        description="Prepare target structures from Captain Stager manifests.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    subcommands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name in ("validate", "inspect", "plan", "apply"):
        command = subcommands.add_parser(name)
        command.add_argument("manifest")
        command.add_argument(
            "--output",
            choices=("text", "json"),
            default="text",
        )

        if name in ("plan", "apply"):
            command.add_argument("--root")
            command.add_argument("--source-root")
            command.add_argument("--target")

        if name == "apply":
            command.add_argument(
                "--dry-run",
                action="store_true",
            )
            command.add_argument(
                "--force",
                action="store_true",
            )

    return parser


def manifest_dict(manifest):
    return {
        "id": manifest.id,
        "name": manifest.name,
        "version": manifest.version,
        "defaultRoot": manifest.default_root,
        "sourceRoot": manifest.source_root,
        "variables": manifest.variables,
        "directoryCount": len(manifest.directories),
        "fileCount": len(manifest.files),
        "copyCount": len(manifest.copies),
        "sourcePath": str(manifest.source_path),
    }


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        if args.command == "validate":
            manifest = validate(args.manifest)
            payload = {
                "valid": True,
                "manifest": manifest_dict(manifest),
            }

            if args.output == "json":
                emit_json(payload)
            else:
                print(
                    f"Valid manifest: {manifest.id} {manifest.version}"
                )

            return 0

        if args.command == "inspect":
            manifest = validate(args.manifest)
            payload = {
                **manifest_dict(manifest),
                "directories": [
                    {
                        "path": directory.path,
                        "mode": directory.mode,
                    }
                    for directory in manifest.directories
                ],
                "files": [
                    {
                        "path": file.path,
                        "encoding": file.encoding,
                        "overwrite": file.overwrite,
                        "mode": file.mode,
                    }
                    for file in manifest.files
                ],
                "copies": [
                    {
                        "source": copy.source,
                        "path": copy.path,
                        "overwrite": copy.overwrite,
                        "mode": copy.mode,
                    }
                    for copy in manifest.copies
                ],
            }

            if args.output == "json":
                emit_json(payload)
            else:
                print(
                    json.dumps(
                        payload,
                        indent=2,
                    )
                )

            return 0

        if args.command == "plan":
            manifest, root, operations = plan(
                args.manifest,
                args.root,
                target_name=args.target,
                source_root_override=args.source_root,
            )

            payload = {
                "manifestId": manifest.id,
                "root": str(root),
                "dryRun": True,
                "succeeded": True,
                "counts": {
                    "planned": len(operations)
                },
                "operations": [
                    {
                        "kind": operation.kind,
                        "relativePath": operation.relative_path,
                        "targetPath": str(operation.target_path),
                        "sourcePath": (
                            str(operation.source_path)
                            if operation.source_path is not None
                            else None
                        ),
                        "status": "planned",
                        "message": None,
                    }
                    for operation in operations
                ],
            }

            if args.output == "json":
                emit_json(payload)
            else:
                print_report(payload)

            return 0

        if args.command == "apply":
            report = apply(
                args.manifest,
                root_override=args.root,
                target_name=args.target,
                source_root_override=args.source_root,
                dry_run=args.dry_run,
                force=args.force,
            )

            payload = report.to_dict()

            if args.output == "json":
                emit_json(payload)
            else:
                print_report(payload)

            return 0 if report.succeeded else 1

    except CaptainCoreError as error:
        payload = {
            "succeeded": False,
            "error": str(error),
        }

        if getattr(args, "output", "text") == "json":
            emit_json(payload)
        else:
            print(
                f"stager: {error}",
                file=sys.stderr,
            )

        return 2

    return 2
