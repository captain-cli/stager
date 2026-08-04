import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from captain_stager.cli import main


class CliErrorTests(unittest.TestCase):
    def test_core_manifest_error_is_reported_as_json_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "wrong-tool.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "header": {
                            "id": "wrong-tool",
                            "name": "Wrong Tool",
                            "tool": "schemawright",
                            "category": "database",
                            "schemaVersion": "1.0",
                            "manifestVersion": "1.0.0",
                        }
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    ["validate", str(manifest_path), "--output", "json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 2)
            self.assertFalse(payload["succeeded"])
            self.assertIn("belongs to tool", payload["error"])
            self.assertEqual(stderr.getvalue(), "")

    def test_core_manifest_error_is_reported_as_text_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "invalid.json"
            manifest_path.write_text("{}", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["validate", str(manifest_path)])

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("stager:", stderr.getvalue())
            self.assertIn('property "header"', stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
