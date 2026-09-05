import tempfile
import unittest
from pathlib import Path

from captain_core.models import ManifestHeader
from captain_core.errors import ManifestError
from captain_core.manifests import parse_manifest_header
from captain_stager.manifest import parse_manifest_document
from captain_stager.models import DirectorySpec

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
                (
                    DirectorySpec(
                        path="Users/demo/Documents",
                    ),
                ),
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

    def test_parses_file_mode(self):
        manifest = parse_manifest_document(
            {
                "files": [
                    {
                        "path": "bin/example",
                        "content": "hello",
                        "mode": "0755",
                    }
                ]
            },
            header=ManifestHeader(
                id="test",
                name="Test Manifest",
                tool="stager",
                category="filesystems",
                schema_version="1.0",
                manifest_version="1.0.0",
            ),
            source_path=Path("/tmp/stager.json"),
        )

        self.assertEqual(
            manifest.files[0].mode,
            0o755,
        )

    def test_rejects_invalid_file_mode(self):
        with self.assertRaises(ManifestError):
            parse_manifest_document(
                {
                    "files": [
                        {
                            "path": "bin/example",
                            "content": "hello",
                            "mode": "banana",
                        }
                    ]
                },
                header=ManifestHeader(
                    id="test",
                    name="Test Manifest",
                    tool="stager",
                    category="filesystems",
                    schema_version="1.0",
                    manifest_version="1.0.0",
                ),
                source_path=Path("/tmp/stager.json"),
            )

    def test_parses_platform_target(self):
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
                        "opt/${app}",
                        "etc/${app}"
                    ],
                    "files": [
                        {
                            "path": "etc/${app}/runtime.conf",
                            "content": "application=${app}"
                        }
                    ],
                    "copies": [
                        {
                            "source": "bin/vibrancy",
                            "path": "usr/bin/${app}"
                        }
                    ]
                }
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "m.json"

            manifest = parse_manifest_document(
                document,
                header=parse_manifest_header(document),
                source_path=source,
            )

            self.assertIn(
                "linux",
                manifest.targets,
            )

            self.assertEqual(
                manifest.targets["linux"].variables["app"],
                "vibrancy",
            )

            self.assertEqual(
                manifest.targets["linux"].default_root,
                "/tmp/stager-linux",
            )

            self.assertEqual(
                manifest.targets["linux"].directories,
                (
                    DirectorySpec(
                        path="opt/vibrancy",
                    ),
                    DirectorySpec(
                        path="etc/vibrancy",
                    ),
                ),
            )

            self.assertEqual(
                manifest.targets["linux"].files[0].path,
                "etc/vibrancy/runtime.conf",
            )

            self.assertEqual(
                manifest.targets["linux"].files[0].content,
                "application=vibrancy",
            )

            self.assertEqual(
                manifest.targets["linux"].copies[0].source,
                "bin/vibrancy",
            )

            self.assertEqual(
                manifest.targets["linux"].copies[0].path,
                "usr/bin/vibrancy",
            )

    def test_parses_directory_mode(self):
        manifest = parse_manifest_document(
            {
                "directories": [
                    {
                        "path": "etc/vibrancy",
                        "mode": "0755",
                    }
                ]
            },
            header=ManifestHeader(
                id="test",
                name="Test Manifest",
                tool="stager",
                category="filesystems",
                schema_version="1.0",
                manifest_version="1.0.0",
            ),
            source_path=Path("/tmp/stager.json"),
        )

        self.assertEqual(
            manifest.directories,
            (
                DirectorySpec(
                    path="etc/vibrancy",
                    mode=0o755,
                ),
            ),
        )