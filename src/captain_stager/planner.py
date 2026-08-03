from pathlib import Path
from .models import Manifest, Operation
from .paths import resolve_inside_root

def build_plan(manifest:Manifest,root:Path)->list[Operation]:
    ops=[Operation('mkdir',d,resolve_inside_root(root,d)) for d in manifest.directories]
    ops += [Operation('write',f.path,resolve_inside_root(root,f.path),f.content,f.encoding,f.overwrite) for f in manifest.files]
    return ops
