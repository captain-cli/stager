import tempfile
import unittest
from pathlib import Path

from captain_core.errors import ManifestError
from captain_core.manifests import parse_manifest_header
from captain_stager.manifest import parse_manifest_document


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

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "m.json"
            manifest = parse_manifest_document(
                document,
                header=parse_manifest_header(document),
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

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "m.json"

            with self.assertRaises(ManifestError):
                parse_manifest_document(
                    document,
                    header=parse_manifest_header(document),
                    source_path=source,
                )
