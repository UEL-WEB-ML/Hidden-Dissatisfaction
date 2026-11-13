"""Filesystem adapter for the modelling item export."""

import json
import os
import subprocess
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from hidden_dissatisfaction.application.modelling_export import (
    ModellingExportContract,
    ModellingExportMetadata,
    normalize_item_records,
    validate_item_records,
)

DEFAULT_EXPORT_CONTRACT = ModellingExportContract()


def export_gold_modelling_items(
    reader: Any,
    metadata: ModellingExportMetadata,
    output_path: str | Path = "data/processed/modelling_items.parquet",
    contract: ModellingExportContract = DEFAULT_EXPORT_CONTRACT,
) -> Path:
    """Export through the Gold reader port, keeping retrieval separate from storage."""
    return export_modelling_items(reader.read_modelling_items(), metadata, output_path, contract)


def _git_sha(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=2
            ).stdout.strip()
            or "unknown"
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _atomic_path(path: Path) -> tuple[int, Path]:
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    return handle, Path(name)


def export_modelling_items(
    records: Iterable[Mapping[str, Any]],
    metadata: ModellingExportMetadata,
    output_path: str | Path = "data/processed/modelling_items.parquet",
    contract: ModellingExportContract = DEFAULT_EXPORT_CONTRACT,
) -> Path:
    """Validate records and atomically publish parquet plus a JSON manifest."""
    import pandas as pd

    rows = validate_item_records(normalize_item_records(records), contract)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = destination.with_suffix(destination.suffix + ".manifest.json")
    parquet_handle, parquet_tmp = _atomic_path(destination)
    manifest_handle, manifest_tmp = _atomic_path(manifest_path)
    try:
        os.close(parquet_handle)
        os.close(manifest_handle)
        frame = pd.DataFrame(rows)
        frame.to_parquet(parquet_tmp, index=False)
        manifest = {
            "source_run_id": metadata.source_run_id,
            "source_hashes": dict(metadata.source_hashes),
            "row_count": len(frame),
            "order_count": frame[contract.order_key].nunique(dropna=False),
            "schema": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            "null_profile": {column: int(value) for column, value in frame.isna().sum().items()},
            "cutoff_version": metadata.cutoff_version,
            "review_policy_version": metadata.review_policy_version,
            "feature_schema_version": metadata.feature_schema_version,
            "git_sha": _git_sha(metadata.git_sha),
        }
        manifest_tmp.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # Publish the pair as a transaction: if the second rename fails, restore
        # the prior pair (or remove the first new member). Readers never observe
        # a newly-created parquet paired with an old manifest.
        old_parquet = destination.with_name(f".{destination.name}.previous")
        old_manifest = manifest_path.with_name(f".{manifest_path.name}.previous")
        had_parquet = destination.exists()
        had_manifest = manifest_path.exists()
        if had_parquet:
            os.replace(destination, old_parquet)
        if had_manifest:
            os.replace(manifest_path, old_manifest)
        try:
            os.replace(parquet_tmp, destination)
            os.replace(manifest_tmp, manifest_path)
        except Exception:
            if destination.exists():
                destination.unlink()
            if manifest_path.exists():
                manifest_path.unlink()
            if had_parquet:
                os.replace(old_parquet, destination)
            if had_manifest:
                os.replace(old_manifest, manifest_path)
            raise
        else:
            for previous in (old_parquet, old_manifest):
                try:
                    previous.unlink()
                except FileNotFoundError:
                    pass
        return destination
    finally:
        for temporary in (parquet_tmp, manifest_tmp):
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
