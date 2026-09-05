import tempfile
import unittest
from pathlib import Path

from captain_core.errors import ManifestError
from captain_core.manifests import parse_manifest_header

from captain_stager.manifest import parse_manifest_document
from captain_stager.service import select_target
from captain_stager.models import DirectorySpec

class TargetTests(unittest.TestCase):

    def make_manifest(self):
        document = {
            "header": {
                "id": "target-test",
                "name": "Target Test",
                "tool": "stager",
                "category": "filesystems",
                "schemaVersion": "1.0",
                "manifestVersion": "1.0.0",
            },
            "targets": {
                "linux": {
                    "defaultRoot": "/tmp/stager-linux",
                    "variables": {
                        "app": "vibrancy"
                    },
                    "directories": [
                        "opt/${app}"
                    ],
                    "copies": [
                        {
                            "source": "bin/vibrancy",
                            "path": "usr/bin/${app}"
                        }
                    ]
                }
            }
        }

        directory = tempfile.TemporaryDirectory()
        source = Path(directory.name) / "m.json"

        manifest = parse_manifest_document(
            document,
            header=parse_manifest_header(document),
            source_path=source,
        )

        return directory, manifest

    def test_selects_target(self):
        directory, manifest = self.make_manifest()

        try:
            selected = select_target(
                manifest,
                "linux",
            )

            self.assertEqual(
                selected.default_root,
                "/tmp/stager-linux",
            )

            self.assertEqual(
                selected.directories,
                (
                    DirectorySpec(
                        path="opt/vibrancy",
                    ),
                ),
            )

            self.assertEqual(
                selected.copies[0].path,
                "usr/bin/vibrancy",
            )

            self.assertEqual(
                selected.targets,
                {},
            )
        finally:
            directory.cleanup()

    def test_none_preserves_manifest(self):
        directory, manifest = self.make_manifest()

        try:
            selected = select_target(
                manifest,
                None,
            )

            self.assertIs(
                selected,
                manifest,
            )
        finally:
            directory.cleanup()

    def test_rejects_unknown_target(self):
        directory, manifest = self.make_manifest()

        try:
            with self.assertRaises(ManifestError):
                select_target(
                    manifest,
                    "windows",
                )
        finally:
            directory.cleanup()