import json

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