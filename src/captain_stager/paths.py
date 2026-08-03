from pathlib import Path
from .errors import ManifestError

def validate_relative_path(value: object, field_name: str) -> str:
    if not isinstance(value,str) or not value.strip(): raise ManifestError(f"{field_name} must be a non-empty string.")
    candidate=value.replace("\\","/").strip()
    if candidate.startswith("/"): raise ManifestError(f"{field_name} must be relative: {value}")
    parts=[p for p in candidate.split("/") if p not in ("",".")]
    if any(p==".." for p in parts): raise ManifestError(f"{field_name} escapes the scaffold root: {value}")
    if not parts: raise ManifestError(f"{field_name} resolves to an empty path.")
    return "/".join(parts)

def resolve_inside_root(root: Path, relative_path: str) -> Path:
    resolved_root=root.resolve(); target=(resolved_root/relative_path).resolve()
    if target != resolved_root and resolved_root not in target.parents: raise ManifestError(f"Path escapes scaffold root: {relative_path}")
    return target
