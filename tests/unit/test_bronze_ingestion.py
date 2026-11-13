import csv
from pathlib import Path

import pytest

from hidden_dissatisfaction.application.bronze_ingestion import (
    BRONZE_FILE_SPECS,
    InvalidBronzeManifest,
    build_manifest,
    iter_csv_rows,
    validate_manifest,
)


def write_raw_fixture(directory: Path) -> None:
    """Create the minimal valid nine-file Olist snapshot."""

    for spec in BRONZE_FILE_SPECS:
        with (directory / spec.filename).open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(spec.headers)
            writer.writerow(["" for _ in spec.headers])


def test_manifest_validates_exact_headers_hashes_and_null_rows(tmp_path: Path) -> None:
    write_raw_fixture(tmp_path)

    manifest = build_manifest(tmp_path)

    validate_manifest(tmp_path, manifest)
    spec = BRONZE_FILE_SPECS[0]
    assert list(iter_csv_rows(tmp_path / spec.filename, spec.headers)) == [
        tuple(None for _ in spec.headers)
    ]


def test_manifest_rejects_missing_unexpected_and_changed_files(tmp_path: Path) -> None:
    write_raw_fixture(tmp_path)
    (tmp_path / BRONZE_FILE_SPECS[0].filename).unlink()
    with pytest.raises(InvalidBronzeManifest, match="missing raw file"):
        build_manifest(tmp_path)

    write_raw_fixture(tmp_path)
    (tmp_path / "unexpected.csv").write_text("a\n", encoding="utf-8")
    with pytest.raises(InvalidBronzeManifest, match="unexpected raw CSV"):
        build_manifest(tmp_path)

    (tmp_path / "unexpected.csv").unlink()
    manifest = build_manifest(tmp_path)
    (tmp_path / BRONZE_FILE_SPECS[0].filename).write_text("wrong\n", encoding="utf-8")
    with pytest.raises(InvalidBronzeManifest, match="unexpected header"):
        validate_manifest(tmp_path, manifest)


def test_manifest_rejects_duplicate_entry_and_wrong_table_or_checksum(tmp_path: Path) -> None:
    write_raw_fixture(tmp_path)
    manifest = build_manifest(tmp_path)
    files = manifest["files"]
    assert isinstance(files, list)
    manifest["files"] = [*files, files[0]]
    with pytest.raises(InvalidBronzeManifest, match="duplicate manifest entry"):
        validate_manifest(tmp_path, manifest)

    manifest = build_manifest(tmp_path)
    files = manifest["files"]
    assert isinstance(files, list)
    first = files[0]
    assert isinstance(first, dict)
    first["table"] = "not_allowlisted"
    with pytest.raises(InvalidBronzeManifest, match="unexpected Bronze table"):
        validate_manifest(tmp_path, manifest)

    manifest = build_manifest(tmp_path)
    files = manifest["files"]
    assert isinstance(files, list)
    first = files[0]
    assert isinstance(first, dict)
    first["sha256"] = "0" * 64
    with pytest.raises(InvalidBronzeManifest, match="checksum mismatch"):
        validate_manifest(tmp_path, manifest)


def test_manifest_and_csv_reject_invalid_shapes(tmp_path: Path) -> None:
    write_raw_fixture(tmp_path)
    manifest = build_manifest(tmp_path)

    manifest["manifest_version"] = 2
    with pytest.raises(InvalidBronzeManifest, match="manifest_version"):
        validate_manifest(tmp_path, manifest)
    manifest["manifest_version"] = 1
    manifest["files"] = {}
    with pytest.raises(InvalidBronzeManifest, match="files must be a list"):
        validate_manifest(tmp_path, manifest)
    manifest["files"] = [{}]
    with pytest.raises(InvalidBronzeManifest, match="requires a name"):
        validate_manifest(tmp_path, manifest)
    manifest = build_manifest(tmp_path)
    files = manifest["files"]
    assert isinstance(files, list)
    manifest["files"] = files[:-1]
    with pytest.raises(InvalidBronzeManifest, match="exactly the nine"):
        validate_manifest(tmp_path, manifest)

    spec = BRONZE_FILE_SPECS[0]
    path = tmp_path / spec.filename
    path.write_text("wrong\n", encoding="utf-8")
    with pytest.raises(InvalidBronzeManifest, match="unexpected header"):
        list(iter_csv_rows(path, spec.headers))
    path.write_text(
        ",".join(spec.headers) + "\n" + ",".join("x" for _ in spec.headers) + ",x\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidBronzeManifest, match="malformed CSV row"):
        list(iter_csv_rows(path, spec.headers))
