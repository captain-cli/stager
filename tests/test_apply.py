import json
import tempfile
import unittest
import stat
from pathlib import Path

from captain_stager.executor import execute_plan
from captain_stager.models import Operation
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

    def test_apply_sets_file_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / "output"
            target = root / "bin/example"

            op = Operation(
                kind="write",
                relative_path="bin/example",
                target_path=target,
                content="hello",
                mode=0o755,
            )

            report = execute_plan(
                "mode-test",
                root,
                [op],
            )

            self.assertEqual(
                stat.S_IMODE(target.stat().st_mode),
                0o755,
            )

            self.assertEqual(
                report.results[0].status,
                "written",
            )

    def test_apply_directory_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / "target"
            manifest = temporary / "m.json"

            manifest.write_text(
                json.dumps(
                    manifest_document(
                        directories=[
                            {
                                "path": "etc/vibrancy",
                                "mode": "0755",
                            }
                        ],
                    )
                ),
                encoding="utf-8",
            )

            report = apply(
                str(manifest),
                root_override=str(root),
            )

            self.assertTrue(report.succeeded)

            mode = stat.S_IMODE(
                (root / "etc/vibrancy").stat().st_mode
            )

            self.assertEqual(
                mode,
                0o755,
            )
