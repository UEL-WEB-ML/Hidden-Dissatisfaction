from collections.abc import Iterator
from pathlib import Path
from typing import Any

from hidden_dissatisfaction.application.modelling_export import ModellingExportMetadata
from hidden_dissatisfaction.infrastructure.modelling_parquet_exporter import (
    export_gold_modelling_items,
)


class Reader:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.called = False

    def read_modelling_items(self) -> Iterator[dict[str, Any]]:
        self.called = True
        return iter(self.rows)


def test_gold_export_delegates_record_retrieval(tmp_path: Path, monkeypatch: Any) -> None:
    reader = Reader([])
    called: list[object] = []

    def fake_export(
        records: object, metadata: object, output_path: object, contract: object
    ) -> Path:
        called.append(records)
        return tmp_path / "x"

    monkeypatch.setattr(
        "hidden_dissatisfaction.infrastructure.modelling_parquet_exporter.export_modelling_items",
        fake_export,
    )
    export_gold_modelling_items(
        reader, ModellingExportMetadata("run", {}, "c", "r", "f"), tmp_path / "x"
    )
    assert reader.called
    assert len(called) == 1
