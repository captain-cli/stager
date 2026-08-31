from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
OperationKind = Literal["mkdir", "write", "copy"]
@dataclass(frozen=True)
class FileSpec:
    path: str
    content: str = ""
    encoding: str = "utf-8"
    overwrite: bool = False
@dataclass(frozen=True)
class CopySpec:
    source: str
    path: str
    overwrite: bool = False
@dataclass(frozen=True)
class Manifest:
    id: str
    name: str
    version: str
    default_root: str | None
    variables: dict[str, str]
    directories: tuple[str, ...]
    files: tuple[FileSpec, ...]
    copies: tuple[CopySpec, ...]
    source_path: Path
@dataclass(frozen=True)
class Operation:
    kind: OperationKind
    relative_path: str
    target_path: Path
    content: str | None = None
    encoding: str = "utf-8"
    overwrite: bool = False
    source_path: Path | None = None
@dataclass
class OperationResult:
    kind: OperationKind
    relative_path: str
    target_path: str
    status: Literal["created", "written", "skipped", "planned", "failed"]
    message: str | None = None
    def to_dict(self) -> dict[str, Any]:
        return {"kind":self.kind,"relativePath":self.relative_path,"targetPath":self.target_path,"status":self.status,"message":self.message}
@dataclass
class ExecutionReport:
    manifest_id: str
    root: str
    dry_run: bool
    results: list[OperationResult] = field(default_factory=list)
    @property
    def succeeded(self) -> bool:
        return not any(r.status == "failed" for r in self.results)
    def to_dict(self) -> dict[str, Any]:
        counts: dict[str,int] = {}
        for r in self.results: counts[r.status] = counts.get(r.status,0)+1
        return {"manifestId":self.manifest_id,"root":self.root,"dryRun":self.dry_run,"succeeded":self.succeeded,"counts":counts,"operations":[r.to_dict() for r in self.results]}
