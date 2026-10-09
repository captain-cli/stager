from pathlib import Path
import shutil

from .models import ExecutionReport, Operation, OperationResult

def ensure_directories(path: Path, root: Path) -> None:
    """Create missing directories with deterministic 0755 permissions."""
    path = path.absolute()
    root = root.absolute()

    if not path.is_relative_to(root):
        raise ValueError(f"Directory outside staging root: {path}")

    missing = []
    current = path

    while not current.exists():
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent

    for directory in reversed(missing):
        directory.mkdir(mode=0o755)
        directory.chmod(0o755)

    if not path.is_dir():
        raise NotADirectoryError(path)

def execute_plan(
        manifest_id: str,
        root: Path,
        operations: list[Operation],
        *,
        dry_run: bool = False,
        force: bool = False,
) -> ExecutionReport:
    report = ExecutionReport(manifest_id, str(root), dry_run)

    if not dry_run:
        ensure_directories(root, root)

    for op in operations:
        try:
            if dry_run:
                report.results.append(
                    OperationResult(
                        op.kind,
                        op.relative_path,
                        str(op.target_path),
                        "planned",
                    )
                )
                continue

            if op.kind == "mkdir":
                ensure_directories(op.target_path, root)

                if op.mode is not None:
                    op.target_path.chmod(op.mode)

                report.results.append(
                    OperationResult(
                        "mkdir",
                        op.relative_path,
                        str(op.target_path),
                        "created",
                    )
                )
                continue

            if op.kind == "write":
                ensure_directories(op.target_path.parent, root)

                if op.target_path.exists() and not (force or op.overwrite):
                    report.results.append(
                        OperationResult(
                            "write",
                            op.relative_path,
                            str(op.target_path),
                            "skipped",
                            "File already exists.",
                        )
                    )
                    continue

                op.target_path.write_text(
                    op.content or "",
                    encoding=op.encoding,
                    )

                if op.mode is not None:
                    op.target_path.chmod(op.mode)

                report.results.append(
                    OperationResult(
                        "write",
                        op.relative_path,
                        str(op.target_path),
                        "written",
                    )
                )
                continue

            if op.kind == "copy":
                if op.source_path is None:
                    report.results.append(
                        OperationResult(
                            "copy",
                            op.relative_path,
                            str(op.target_path),
                            "failed",
                            "Copy operation has no source path.",
                        )
                    )
                    continue

                if not op.source_path.exists():
                    report.results.append(
                        OperationResult(
                            "copy",
                            op.relative_path,
                            str(op.target_path),
                            "failed",
                            f"Copy source does not exist: {op.source_path}",
                        )
                    )
                    continue

                if op.target_path.exists() and not (force or op.overwrite):
                    report.results.append(
                        OperationResult(
                            "copy",
                            op.relative_path,
                            str(op.target_path),
                            "skipped",
                            "Destination already exists.",
                        )
                    )
                    continue

                if op.source_path.is_file():
                    ensure_directories(op.target_path.parent, root)

                    shutil.copy2(
                        op.source_path,
                        op.target_path,
                    )

                elif op.source_path.is_dir():
                    if op.target_path.exists():
                        shutil.rmtree(op.target_path)

                    ensure_directories(op.target_path.parent, root)

                    shutil.copytree(
                        op.source_path,
                        op.target_path,
                        copy_function=shutil.copy2,
                    )

                else:
                    report.results.append(
                        OperationResult(
                            "copy",
                            op.relative_path,
                            str(op.target_path),
                            "failed",
                            f"Unsupported copy source: {op.source_path}",
                        )
                    )
                    continue

                if op.mode is not None:
                    op.target_path.chmod(op.mode)

                report.results.append(
                    OperationResult(
                        "copy",
                        op.relative_path,
                        str(op.target_path),
                        "written",
                    )
                )
                continue

            report.results.append(
                OperationResult(
                    op.kind,
                    op.relative_path,
                    str(op.target_path),
                    "failed",
                    f"Unsupported operation: {op.kind}",
                )
            )

        except OSError as e:
            report.results.append(
                OperationResult(
                    op.kind,
                    op.relative_path,
                    str(op.target_path),
                    "failed",
                    str(e),
                )
            )

    return report