"""Safe loading and validation of released joblib model envelopes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import joblib

from hidden_dissatisfaction.modeling.schema import FEATURES, MODEL_INPUT_SCHEMA_VERSION


class ModelArtifactError(ValueError):
    pass


def load_model_artifact(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise ModelArtifactError("model artifact hash mismatch")
    # Hash verification deliberately precedes deserialization.
    loaded = joblib.load(path)
    if not isinstance(loaded, dict):
        raise ModelArtifactError("model artifact must be an envelope")
    required = {
        "kind",
        "artifact_format_version",
        "model_input_schema_version",
        "feature_names",
        "estimator",
    }
    if set(loaded) != required or loaded["kind"] != "HIDDEN_DISSATISFACTION_MODEL":
        raise ModelArtifactError("invalid model artifact envelope")
    if (
        loaded["artifact_format_version"] != 1
        or loaded["model_input_schema_version"] != MODEL_INPUT_SCHEMA_VERSION
    ):
        raise ModelArtifactError("unsupported model artifact version")
    if not isinstance(loaded["feature_names"], (list, tuple)):
        raise ModelArtifactError("model artifact feature schema mismatch")
    if tuple(loaded["feature_names"]) != FEATURES:
        raise ModelArtifactError("model artifact feature schema mismatch")
    return loaded


class JoblibModelArtifactLoader:
    def load(self, path: Path, expected_sha256: str) -> dict[str, Any]:
        return load_model_artifact(path, expected_sha256)
