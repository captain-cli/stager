import json
import tempfile
import unittest
from pathlib import Path

from captain_core.errors import ManifestError, ManifestOwnershipError
from captain_stager.service import load_project_manifest


def captain_manifest(*, inline=None, reference=None):
    document = {
        "schema": "captain/manifest/v1",
        "project": {"name": "sample", "type": "native", "version": "1.2.3"},
        "versionLanes": {},
        "components": [],
    }
    if inline is not None:
        document["stager"] = inline
    if reference is not None:
        document["manifests"] = {"stager": reference}
    return document


class CaptainProjectManifestTests(unittest.TestCase):
    def write(self, path: Path, document: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")

    def test_loads_inline_stager_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "manifest.json", captain_manifest(inline={
                "defaultRoot": "/tmp/sample",
                "directories": ["usr/bin"],
            }))
            manifest = load_project_manifest(root)
            self.assertEqual(manifest.id, "sample")
            self.assertEqual(manifest.version, "1.2.3")
            self.assertEqual(manifest.directories[0].path, "usr/bin")
            self.assertEqual(manifest.source_path, (root / "manifest.json").resolve())

    def test_loads_split_stager_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "manifest.json", captain_manifest(reference="manifests/stager.json"))
            self.write(root / "manifests/stager.json", {
                "schema": "captain/tool-manifest/v1",
                "tool": "stager",
                "config": {"directories": ["etc/sample"]},
            })
            manifest = load_project_manifest(root)
            self.assertEqual(manifest.directories[0].path, "etc/sample")
            self.assertEqual(manifest.source_path, (root / "manifest.json").resolve())

    def test_split_sources_are_project_relative_not_manifest_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "manifest.json", captain_manifest(reference="manifests/stager.json"))
            self.write(root / "manifests/stager.json", {
                "schema": "captain/tool-manifest/v1",
                "tool": "stager",
                "config": {"copies": [{"source": "dist/app", "path": "usr/bin/app"}]},
            })
            manifest = load_project_manifest(root)
            self.assertEqual(manifest.source_path.parent, root.resolve())

    def test_rejects_wrong_split_owner_before_stager_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "manifest.json", captain_manifest(reference="manifests/stager.json"))
            self.write(root / "manifests/stager.json", {
                "schema": "captain/tool-manifest/v1",
                "tool": "embark",
                "config": {},
            })
            with self.assertRaises(ManifestOwnershipError):
                load_project_manifest(root)

    def test_stager_still_validates_resolved_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "manifest.json", captain_manifest(inline={
                "directories": ["${missing}/bin"],
            }))
            with self.assertRaisesRegex(ManifestError, "undefined variable"):
                load_project_manifest(root)


if __name__ == "__main__":
    unittest.main()
