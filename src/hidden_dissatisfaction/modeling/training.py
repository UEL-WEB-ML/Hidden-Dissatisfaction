"""End-to-end orchestration for temporal model selection, calibration, and evaluation."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import average_precision_score, brier_score_loss

from hidden_dissatisfaction.modeling.estimators import build_candidates
from hidden_dissatisfaction.modeling.evaluation import (
    bootstrap_average_precision,
    budget_metrics,
    classification_metrics,
    select_f1_threshold,
)
from hidden_dissatisfaction.modeling.schema import (
    FEATURES,
    TARGET,
    VALUE_COLUMN,
    validate_modeling_table,
)
from hidden_dissatisfaction.modeling.splitting import partition_summary, temporal_split


@dataclass(frozen=True)
class TrainingConfig:
    """Explicit boundaries and reproducibility controls for one experiment."""

    validation_start: datetime = datetime(2018, 1, 1)
    test_start: datetime = datetime(2018, 4, 1)
    test_end: datetime = datetime(2018, 9, 1)
    seed: int = 42
    budgets: tuple[float, ...] = (0.05, 0.10, 0.20)
    bootstrap_iterations: int = 1_000

    @classmethod
    def from_toml(cls, path: Path) -> TrainingConfig:
        """Load the versioned experiment boundaries and evaluation settings."""
        with path.open("rb") as source:
            raw = tomllib.load(source)
        validation = raw["validation"]
        evaluation = raw["evaluation"]
        project = raw["project"]
        return cls(
            validation_start=datetime.fromisoformat(validation["validation_start"]),
            test_start=datetime.fromisoformat(validation["test_start"]),
            test_end=datetime.fromisoformat(validation["test_end"]),
            seed=int(project["random_seed"]),
            budgets=tuple(float(value) for value in evaluation["budgets"]),
            bootstrap_iterations=int(evaluation["bootstrap_iterations"]),
        )


def run_training(
    data_path: Path,
    *,
    config: TrainingConfig | None = None,
    output_root: Path = Path("."),
) -> dict[str, Any]:
    """Run the declared experiment and persist auditable local artifacts."""
    settings = config or TrainingConfig()
    frame = validate_modeling_table(_read_table(data_path))
    partitions = temporal_split(
        frame,
        validation_start=settings.validation_start,
        test_start=settings.test_start,
        test_end=settings.test_end,
    )

    X_train, y_train = partitions.train.loc[:, FEATURES], partitions.train[TARGET]
    X_selection, y_selection = partitions.selection.loc[:, FEATURES], partitions.selection[TARGET]
    selection_scores: dict[str, float] = {}
    for name, estimator in build_candidates(settings.seed).items():
        estimator.fit(X_train, y_train)
        probability = estimator.predict_proba(X_selection)[:, 1]
        selection_scores[name] = float(average_precision_score(y_selection, probability))

    eligible = {name: score for name, score in selection_scores.items() if name != "prevalence"}
    selected_name = max(eligible, key=eligible.__getitem__)
    selected = build_candidates(settings.seed)[selected_name]
    development = pd.concat([partitions.train, partitions.selection], ignore_index=True)
    selected.fit(development.loc[:, FEATURES], development[TARGET])

    calibration_midpoint = len(partitions.calibration) // 2
    calibration_fit = partitions.calibration.iloc[:calibration_midpoint]
    calibration_evaluation = partitions.calibration.iloc[calibration_midpoint:]
    X_calibration_fit = calibration_fit.loc[:, FEATURES]
    y_calibration_fit = calibration_fit[TARGET]
    X_calibration_evaluation = calibration_evaluation.loc[:, FEATURES]
    y_calibration_evaluation = calibration_evaluation[TARGET]
    selected, calibration_method, calibration_scores = _select_calibration(
        selected,
        X_calibration_fit,
        y_calibration_fit,
        X_calibration_evaluation,
        y_calibration_evaluation,
    )
    calibration_probability = selected.predict_proba(X_calibration_evaluation)[:, 1]
    threshold = select_f1_threshold(y_calibration_evaluation, calibration_probability)

    X_test = partitions.test.loc[:, FEATURES]
    y_test = partitions.test[TARGET]
    test_probability = selected.predict_proba(X_test)[:, 1]
    metrics = classification_metrics(y_test, test_probability, threshold)
    metrics["average_precision_ci"] = bootstrap_average_precision(  # type: ignore[assignment]
        y_test,
        test_probability,
        iterations=settings.bootstrap_iterations,
        seed=settings.seed,
    )
    priorities = budget_metrics(
        y_test,
        test_probability,
        partitions.test[VALUE_COLUMN],
        settings.budgets,
    )

    predictions = partitions.test[
        ["order_id", "order_delivered_customer_date", TARGET, VALUE_COLUMN]
    ].copy()
    predictions["predicted_probability"] = test_probability
    predictions["predicted_label"] = (test_probability >= threshold).astype(int)

    report: dict[str, Any] = {
        "data": {
            "path": str(data_path),
            "sha256": _sha256(data_path),
            "rows": len(frame),
        },
        "config": _json_safe_config(settings),
        "partitions": partition_summary(partitions),
        "selection_average_precision": selection_scores,
        "selected_model": selected_name,
        "calibration_method": calibration_method,
        "calibration_brier_scores": calibration_scores,
        "test_metrics": metrics,
        "budget_metrics": priorities,
    }
    _write_artifacts(output_root, selected, predictions, report)
    return report


def _select_calibration(
    estimator: BaseEstimator,
    X_fit: pd.DataFrame,
    y_fit: pd.Series,
    X_evaluation: pd.DataFrame,
    y_evaluation: pd.Series,
) -> tuple[BaseEstimator, str, dict[str, float]]:
    raw_probability = estimator.predict_proba(X_evaluation)[:, 1]
    candidates: dict[str, BaseEstimator] = {"none": estimator}
    scores = {"none": float(brier_score_loss(y_evaluation, raw_probability))}
    for method in ("sigmoid", "isotonic"):
        calibrated = CalibratedClassifierCV(FrozenEstimator(estimator), method=method)
        calibrated.fit(X_fit, y_fit)
        candidates[method] = calibrated
        scores[method] = float(
            brier_score_loss(y_evaluation, calibrated.predict_proba(X_evaluation)[:, 1])
        )
    chosen = min(scores, key=scores.__getitem__)
    return candidates[chosen], chosen, scores


def _read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Modeling dataset not found: {path}")
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError("Modeling dataset must be .parquet or .csv")


def _write_artifacts(
    root: Path, estimator: BaseEstimator, predictions: pd.DataFrame, report: dict[str, Any]
) -> None:
    model_path = root / "artifacts/models/hidden_dissatisfaction.joblib"
    prediction_path = root / "artifacts/predictions/test_predictions.csv"
    report_path = root / "reports/experiments/latest.json"
    for path in (model_path, prediction_path, report_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(estimator, model_path)
    predictions.to_csv(prediction_path, index=False)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_safe_config(config: TrainingConfig) -> dict[str, object]:
    return {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in asdict(config).items()
    }
