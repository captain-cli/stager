import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from captain_core.errors import (
    CaptainProjectNotFoundError,
    ManifestError,
    ManifestNotFoundError,
    ManifestOwnershipError,
)
from captain_stager.service import load_resolved_manifest
from captain_stager.models import DirectorySpec

def manifest_document(*, tool="stager", directories=None, files=None, header_patch=None):
    header = {
        "id": "integration-test",
        "name": "Integration Test",
        "tool": tool,
        "category": "filesystems",
        "schemaVersion": "1.0",
        "manifestVersion": "1.0.0",
    }
    if header_patch:
        header.update(header_patch)
    return {
        "header": header,
        "directories": directories or [],
        "files": files or [],
    }


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class CaptainCoreManifestIntegrationTests(unittest.TestCase):
    def write_manifest(self, path: Path, document: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_loads_explicit_manifest_path(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = self.write_manifest(
                Path(directory) / "explicit.json",
                manifest_document(directories=["System/Applications"]),
            )

            manifest = load_resolved_manifest(str(manifest_path))

            self.assertEqual(manifest.id, "integration-test")
            self.assertEqual(
                manifest.directories,
                (
                    DirectorySpec(
                        path="System/Applications",
                    ),
                ),
            )
            self.assertEqual(manifest.source_path, manifest_path.resolve())

    def test_loads_project_local_manifest_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "project"
            manifest_path = self.write_manifest(
                project_root
                / "captain"
                / "manifests"
                / "stager"
                / "filesystems"
                / "demo.json",
                manifest_document(directories=["Users/demo/Documents"]),
            )
            nested = project_root / "apps" / "desktop"
            nested.mkdir(parents=True)

            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CAPTAIN_ROOT", None)
                with working_directory(nested):
                    manifest = load_resolved_manifest("filesystems/demo")

            self.assertEqual(manifest.source_path, manifest_path.resolve())
            self.assertEqual(
                manifest.directories,
                (
                    DirectorySpec(
                        path="Users/demo/Documents",
                    ),
                ),
            )

    def test_uses_configured_captain_root(self):
        with tempfile.TemporaryDirectory() as directory:
            captain_root = Path(directory) / "shared-captain"
            manifest_path = self.write_manifest(
                captain_root / "manifests" / "stager" / "demo.json",
                manifest_document(directories=["Shared"]),
            )

            with patch.dict(os.environ, {"CAPTAIN_ROOT": str(captain_root)}):
                manifest = load_resolved_manifest("demo")

            self.assertEqual(manifest.source_path, manifest_path.resolve())

    def test_rejects_manifest_owned_by_another_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = self.write_manifest(
                Path(directory) / "wrong-tool.json",
                manifest_document(tool="schemawright"),
            )

            with self.assertRaises(ManifestOwnershipError):
                load_resolved_manifest(str(manifest_path))

    def test_rejects_invalid_common_header(self):
        with tempfile.TemporaryDirectory() as directory:
            document = manifest_document()
            del document["header"]["manifestVersion"]
            manifest_path = self.write_manifest(
                Path(directory) / "invalid-header.json",
                document,
            )

            with self.assertRaisesRegex(ManifestError, "manifestVersion"):
                load_resolved_manifest(str(manifest_path))

    def test_rejects_missing_manifest_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "project"
            (project_root / "captain" / "manifests" / "stager").mkdir(
                parents=True
            )

            with patch.dict(
                os.environ,
                {"CAPTAIN_ROOT": str(project_root / "captain")},
            ):
                with self.assertRaises(ManifestNotFoundError):
                    load_resolved_manifest("filesystems/missing")

    def test_rejects_manifest_reference_that_escapes_tool_root(self):
        with tempfile.TemporaryDirectory() as directory:
            captain_root = Path(directory) / "captain"
            (captain_root / "manifests" / "stager").mkdir(parents=True)

            with patch.dict(os.environ, {"CAPTAIN_ROOT": str(captain_root)}):
                with self.assertRaises(ManifestError):
                    load_resolved_manifest("../schemawright/private")

    def test_requires_captain_project_for_symbolic_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CAPTAIN_ROOT", None)
                with working_directory(Path(directory)):
                    with self.assertRaises(CaptainProjectNotFoundError):
                        load_resolved_manifest("demo")

    def test_stager_body_validation_runs_after_core_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = self.write_manifest(
                Path(directory) / "undefined-variable.json",
                manifest_document(directories=["Users/${missing}/Documents"]),
            )

            with self.assertRaisesRegex(ManifestError, "undefined variable"):
                load_resolved_manifest(str(manifest_path))


if __name__ == "__main__":
    unittest.main()
