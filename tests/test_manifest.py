import tempfile
import unittest
from pathlib import Path

from captain_stager.errors import ManifestError
from captain_stager.manifest import load_manifest_document


class ManifestTests(unittest.TestCase):

    def test_variables(self):
        document = {
            "header": {
                "id": "t",
                "name": "T",
                "tool": "stager",
                "category": "filesystems",
                "schemaVersion": "1.0",
                "manifestVersion": "1.0.0"
            },
            "variables": {
                "user": "demo"
            },
            "directories": [
                "Users/${user}/Documents"
            ],
            "files": [
                {
                    "path": "Users/${user}/Documents/r.txt",
                    "content": "Hello ${user}"
                }
            ]
        }

        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "m.json"

            manifest = load_manifest_document(
                document,
                source_path=source,
            )

            self.assertEqual(
                manifest.directories,
                ("Users/demo/Documents",),
            )

            self.assertEqual(
                manifest.files[0].content,
                "Hello demo",
            )

    def test_rejects_escape(self):
        document = {
            "header": {
                "id": "t",
                "name": "T",
                "tool": "stager",
                "category": "filesystems",
                "schemaVersion": "1.0",
                "manifestVersion": "1.0.0"
            },
            "directories": [
                "../escape"
            ]
        }

        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "m.json"

            with self.assertRaises(ManifestError):
                load_manifest_document(
                    document,
                    source_path=source,
                )