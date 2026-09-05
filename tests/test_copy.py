import json
import stat
import tempfile
from pathlib import Path
from captain_stager.executor import execute_plan
from captain_stager.models import Operation
from captain_stager.service import apply, plan, validate


def write_manifest(tmp_path, *, source="source.txt", destination="usr/share/test/source.txt"):
    manifest_path = tmp_path / "stager.json"

    manifest_path.write_text(
        json.dumps(
            {
                "header": {
                    "id": "copy-test",
                    "name": "Copy Test",
                    "tool": "stager",
                    "category": "filesystems",
                    "schemaVersion": "1.0",
                    "manifestVersion": "1.0.0",
                },
                "defaultRoot": str(tmp_path / "output"),
                "variables": {},
                "directories": [],
                "files": [],
                "copies": [
                    {
                        "source": source,
                        "path": destination,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    return manifest_path


def test_manifest_parses_copy_spec(tmp_path):
    manifest_path = write_manifest(tmp_path)

    manifest = validate(manifest_path)

    assert len(manifest.copies) == 1

    copy = manifest.copies[0]

    assert copy.source == "source.txt"
    assert copy.path == "usr/share/test/source.txt"
    assert copy.overwrite is False


def test_plan_creates_copy_operation(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello from stager", encoding="utf-8")

    manifest_path = write_manifest(tmp_path)

    manifest, root, operations = plan(manifest_path)

    assert len(operations) == 1

    operation = operations[0]

    assert operation.kind == "copy"
    assert operation.relative_path == "usr/share/test/source.txt"
    assert operation.source_path == source
    assert operation.target_path == root / "usr/share/test/source.txt"


def test_apply_copies_existing_file(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello from stager", encoding="utf-8")

    manifest_path = write_manifest(tmp_path)

    report = apply(manifest_path)

    destination = (
            tmp_path
            / "output"
            / "usr"
            / "share"
            / "test"
            / "source.txt"
    )

    assert report.succeeded
    assert destination.is_file()
    assert destination.read_text(encoding="utf-8") == "hello from stager"

    assert len(report.results) == 1
    assert report.results[0].kind == "copy"
    assert report.results[0].status == "written"

def test_apply_copies_directory_recursively(tmp_path):
    source_dir = tmp_path / "runtime"
    source_dir.mkdir()

    (source_dir / "libbass.so").write_text(
        "bass",
        encoding="utf-8",
    )

    nested_dir = source_dir / "plugins"
    nested_dir.mkdir()

    (nested_dir / "libbassflac.so").write_text(
        "flac",
        encoding="utf-8",
    )

    manifest_path = write_manifest(
        tmp_path,
        source="runtime",
        destination="usr/lib/vibrancy",
    )

    report = apply(manifest_path)

    destination = (
            tmp_path
            / "output"
            / "usr"
            / "lib"
            / "vibrancy"
    )

    assert report.succeeded

    assert (
                   destination
                   / "libbass.so"
           ).read_text(encoding="utf-8") == "bass"

    assert (
                   destination
                   / "plugins"
                   / "libbassflac.so"
           ).read_text(encoding="utf-8") == "flac"

    assert len(report.results) == 1
    assert report.results[0].kind == "copy"
    assert report.results[0].status == "written"


def test_apply_fails_when_copy_source_does_not_exist(tmp_path):
    manifest_path = write_manifest(
        tmp_path,
        source="missing.txt",
    )

    report = apply(manifest_path)

    assert not report.succeeded

    assert len(report.results) == 1
    assert report.results[0].kind == "copy"
    assert report.results[0].status == "failed"
    assert "Copy source does not exist" in report.results[0].message


def test_copy_applies_mode(tmp_path):
    source = tmp_path / "source"
    source.write_text("hello")

    root = tmp_path / "root"
    target = root / "usr/bin/example"

    op = Operation(
        kind="copy",
        relative_path="usr/bin/example",
        target_path=target,
        source_path=source,
        mode=0o755,
    )

    report = execute_plan(
        "mode-test",
        root,
        [op],
    )

    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert report.results[0].status == "written"

def test_plan_uses_explicit_source_root(tmp_path):
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()

    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()

    source = artifact_root / "bin" / "example"
    source.parent.mkdir()
    source.write_text("example", encoding="utf-8")

    manifest_path = write_manifest(
        manifest_dir,
        source="bin/example",
        destination="usr/bin/example",
    )

    _, _, operations = plan(
        manifest_path,
        source_root_override=str(artifact_root),
    )

    assert operations[0].source_path == source.resolve()


def test_manifest_rejects_copy_source_escape(tmp_path):
    manifest_path = write_manifest(
        tmp_path,
        source="../../outside.txt",
    )

    try:
        validate(manifest_path)
    except Exception as error:
        assert "copies[0].source" in str(error) or "relative" in str(error).lower()
    else:
        raise AssertionError("escaping copy source should be rejected")
