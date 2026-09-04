from pathlib import Path
from .models import Manifest, Operation
from .paths import resolve_inside_root

def build_plan(manifest: Manifest, root: Path) -> list[Operation]:
    ops = [
        Operation("mkdir", d, resolve_inside_root(root, d))
        for d in manifest.directories
    ]

    ops += [
        Operation(
            kind="write",
            relative_path=f.path,
            target_path=resolve_inside_root(root, f.path),
            content=f.content,
            encoding=f.encoding,
            overwrite=f.overwrite,
            mode=f.mode,
        )
        for f in manifest.files
    ]

    ops += [
        Operation(
            kind="copy",
            relative_path=c.path,
            target_path=resolve_inside_root(root, c.path),
            overwrite=c.overwrite,
            source_path=manifest.source_path.parent / c.source,
            mode=c.mode,
        )
        for c in manifest.copies
    ]

    return ops