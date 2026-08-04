import json
import tempfile
import unittest
from pathlib import Path

from captain_stager.service import apply


def manifest_document(*, directories, files=None):
    return {
        "header": {
            "id": "t",
            "name": "T",
            "tool": "stager",
            "category": "filesystems",
            "schemaVersion": "1.0",
            "manifestVersion": "1.0.0",
        },
        "directories": directories,
        "files": files or [],
    }


class ApplyTests(unittest.TestCase):
    def test_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / "target"
            manifest = temporary / "m.json"
            manifest.write_text(
                json.dumps(
                    manifest_document(
                        directories=["a/b"],
                        files=[{
                            "path": "a/b/r.txt",
                            "content": "ready",
                        }],
                    )
                ),
                encoding="utf-8",
            )

            report = apply(str(manifest), root_override=str(root))

            self.assertTrue(report.succeeded)
            self.assertEqual((root / "a/b/r.txt").read_text(), "ready")

    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / "target"
            manifest = temporary / "m.json"
            manifest.write_text(
                json.dumps(manifest_document(directories=["a"])),
                encoding="utf-8",
            )

            report = apply(
                str(manifest),
                root_override=str(root),
                dry_run=True,
            )

            self.assertFalse(root.exists())
            self.assertEqual(report.results[0].status, "planned")
