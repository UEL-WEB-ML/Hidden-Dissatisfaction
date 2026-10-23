"""End-to-end orchestration for temporal model selection, calibration, and evaluation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import average_precision_score, brier_score_loss

from hidden_dissatisfaction.modeling.estimators import build_candidates
from hidden_dissatisfaction.modeling.evaluation import (
    aggregate_order_predictions,
    bootstrap_average_precision,
    budget_metrics,
    classification_metrics,
    order_classification_metrics,
)
from hidden_dissatisfaction.modeling.schema import (
    CATEGORICAL_FEATURES,
    FEATURES,
    TARGET,
    VALUE_COLUMN,
    validate_modeling_table,
)
from hidden_dissatisfaction.modeling.splitting import (
    grouped_temporal_split,
    partition_summary,
    rolling_origin_splits,
)


@dataclass(frozen=True)
class TrainingConfig:
    """Explicit boundaries and reproducibility controls for one experiment."""

    train_end: datetime = datetime(2017, 10, 1)
    selection_end: datetime = datetime(2017, 12, 1)
    calibration_fit_end: datetime = datetime(2018, 2, 1)
    calibration_compare_end: datetime = datetime(2018, 4, 1)
    threshold_end: datetime = datetime(2018, 6, 1)
    test_end: datetime = datetime(2018, 9, 1)
    # Accepted for callers of the pre-grouped API; partitioning does not use them.
    validation_start: datetime | None = None
    test_start: datetime | None = None
    seed: int = 42
    budgets: tuple[float, ...] = (0.05, 0.10, 0.20)
    bootstrap_iterations: int = 1_000
    rolling_folds: int = 3
    regimes: tuple[str, ...] = ("item_unweighted", "order_weight", "order_reference")

    @classmethod
    def from_toml(cls, path: Path) -> TrainingConfig:
        """Load the versioned experiment boundaries and evaluation settings."""
        with path.open("rb") as source:
            raw = tomllib.load(source)
        validation = raw["validation"]
        evaluation = raw["evaluation"]
        project = raw["project"]
        return cls(
            train_end=datetime.fromisoformat(validation["train_end"]),
            selection_end=datetime.fromisoformat(validation["selection_end"]),
            calibration_fit_end=datetime.fromisoformat(validation["calibration_fit_end"]),
            calibration_compare_end=datetime.fromisoformat(validation["calibration_compare_end"]),
            threshold_end=datetime.fromisoformat(validation["threshold_end"]),
            test_end=datetime.fromisoformat(validation["test_end"]),
            seed=int(project["random_seed"]),
            budgets=tuple(float(value) for value in evaluation["budgets"]),
            bootstrap_iterations=int(evaluation["bootstrap_iterations"]),
            rolling_folds=int(validation["rolling_folds"]),
        )


def run_training(
    data_path: Path,
    *,
    config: TrainingConfig | None = None,
    output_root: Path = Path("."),
    finalize_test: bool = False,
    frozen_selection_record: dict[str, Any] | None = None,
    test_lock: str | None = None,
) -> dict[str, Any]:
    """Run the declared experiment and persist auditable local artifacts."""
    settings = config or TrainingConfig()
    frame = validate_modeling_table(_read_table(data_path))
    partitions = grouped_temporal_split(
        frame,
        boundaries={
            "train": settings.train_end,
            "selection": settings.selection_end,
            "calibration_fit": settings.calibration_fit_end,
            "calibration_compare": settings.calibration_compare_end,
            "threshold": settings.threshold_end,
            "test": settings.test_end,
        },
    )

    development = partitions.train
    folds = rolling_origin_splits(development, n_splits=settings.rolling_folds)
    candidates = build_candidates(settings.seed)
    candidate_names = list(candidates)
    simplicity = {name: index for index, name in enumerate(candidate_names)}
    fold_scores: dict[str, list[dict[str, object]]] = {}
    fold_average_precision: dict[str, list[float]] = {}
    order_brier: dict[str, list[float]] = {}
    order_average_precision: dict[str, list[float]] = {}
    for regime in settings.regimes:
        for name in candidate_names:
            key = f"{regime}:{name}"
            fold_scores[key] = []
            fold_average_precision[key] = []
            order_brier[key] = []
            order_average_precision[key] = []
    for fold_number, (fold_train, fold_validation) in enumerate(folds, start=1):
        X_train, y_train = fold_train.loc[:, FEATURES], fold_train[TARGET]
        X_validation = fold_validation.loc[:, FEATURES]
        y_validation = fold_validation[TARGET]
        for regime in settings.regimes:
            for name in candidate_names:
                key = f"{regime}:{name}"
                estimator = build_candidates(settings.seed)[name]
                estimator.fit(X_train, y_train, **_fit_kwargs(fold_train, regime))
                probability = estimator.predict_proba(X_validation)[:, 1]
                average_precision = float(average_precision_score(y_validation, probability))
                y_metric, order_probability = _order_max(fold_validation, probability)
                fold_average_precision[key].append(average_precision)
                order_average_precision[key].append(
                    float(average_precision_score(y_metric, order_probability))
                )
                order_brier[key].append(float(brier_score_loss(y_metric, order_probability)))
                fold_scores[key].append(
                    {
                        "fold": fold_number,
                        "train_rows": len(fold_train),
                        "validation_rows": len(fold_validation),
                        "validation_start": fold_validation["prediction_at"].min().isoformat(),
                        "validation_end": fold_validation["prediction_at"].max().isoformat(),
                        "average_precision": average_precision,
                        "regime": regime,
                    }
                )

    selection_scores = {
        name: float(np.mean(scores)) for name, scores in fold_average_precision.items()
    }
    selection_standard_deviation = {
        name: float(np.std(scores)) for name, scores in fold_average_precision.items()
    }

    selection_order_pr_auc: dict[str, float] = {}
    selection_order_brier: dict[str, float] = {}
    for regime in settings.regimes:
        for name in candidate_names:
            key = f"{regime}:{name}"
            estimator = build_candidates(settings.seed)[name]
            fit_frame = _training_frame(development, regime)
            estimator.fit(
                fit_frame.loc[:, FEATURES], fit_frame[TARGET], **_fit_kwargs(fit_frame, regime)
            )
            probability = estimator.predict_proba(partitions.selection.loc[:, FEATURES])[:, 1]
            labels, order_probability = _order_max(partitions.selection, probability)
            selection_order_pr_auc[key] = float(average_precision_score(labels, order_probability))
            selection_order_brier[key] = float(brier_score_loss(labels, order_probability))

    selected_key = max(
        selection_order_pr_auc,
        key=lambda k: (
            selection_order_pr_auc[k],
            -selection_order_brier[k],
            -simplicity[k.split(":", 1)[1]],
        ),
    )
    selected_regime, selected_name = selected_key.split(":", 1)
    selected = build_candidates(settings.seed)[selected_name]
    fit_frame = _training_frame(
        pd.concat([development, partitions.selection], ignore_index=True), selected_regime
    )
    selected.fit(
        fit_frame.loc[:, FEATURES], fit_frame[TARGET], **_fit_kwargs(fit_frame, selected_regime)
    )

    calibration_fit = partitions.calibration_fit
    calibration_evaluation = partitions.calibration_compare
    X_calibration_fit = calibration_fit.loc[:, FEATURES]
    y_calibration_fit = cast(pd.Series, calibration_fit[TARGET])
    X_calibration_evaluation = calibration_evaluation.loc[:, FEATURES]
    y_calibration_evaluation = cast(pd.Series, calibration_evaluation[TARGET])
    selected, calibration_method, calibration_scores = _select_calibration(
        selected,
        X_calibration_fit,
        y_calibration_fit,
        X_calibration_evaluation,
        y_calibration_evaluation,
    )
    threshold_probability = selected.predict_proba(partitions.threshold.loc[:, FEATURES])[:, 1]
    threshold = _capacity_thresholds(partitions.threshold, threshold_probability)

    selection_record = {
        "selected_key": selected_key,
        "variant_id": selected_name,
        "variant_parameters": {
            str(k): str(v)
            for k, v in sorted(selected.get_params(deep=True).items())
            if k.startswith("model__")
        },
        "selection_rule": "max order_max_v1_pr_auc, then min Brier, then declared simplicity",
        "calibration_method": calibration_method,
        "threshold_policy": threshold,
        "lock": _selection_lock(selected_key, calibration_method, threshold),
    }
    if finalize_test and (
        frozen_selection_record != selection_record
        or test_lock != selection_record["lock"]
        or "manifest" not in _dataset_hashes(data_path)
    ):
        raise ValueError(
            "test finalization requires a frozen selection record and matching test lock"
        )

    metrics: dict[str, Any] = {}
    priorities: dict[str, Any] = {}
    item_predictions = pd.DataFrame()
    order_predictions = pd.DataFrame()
    test_probability = np.array([])
    if finalize_test:
        # Recovery is attempted before touching the sealed partition.
        _write_attempt_metadata(
            output_root, selection_record, _dataset_hashes(data_path), "started"
        )
        checkpoint = _read_recovery_checkpoint(
            output_root, _dataset_hashes(data_path), cast(str, selection_record["lock"])
        )
        X_test = partitions.test.loc[:, FEATURES]
        y_test = cast(pd.Series, partitions.test[TARGET])
        test_probability = (
            np.asarray(checkpoint["item_predictions"]["priority_score"], dtype=float)
            if checkpoint is not None
            else selected.predict_proba(X_test)[:, 1]
        )
        item_metrics = classification_metrics(
            y_test.tolist(), test_probability.tolist(), threshold["medium_from"]
        )
        item_predictions = (
            pd.DataFrame(checkpoint["item_predictions"])
            if checkpoint is not None
            else partitions.test[
                ["product_item_id", "order_id", "prediction_at", TARGET, VALUE_COLUMN]
                + [c for c in CATEGORICAL_FEATURES if c in partitions.test]
            ].copy()
        )
        item_predictions = item_predictions.rename(
            columns={TARGET: "label", VALUE_COLUMN: "order_value"}
        )
        item_predictions["priority_score"] = test_probability
        order_predictions = (
            pd.DataFrame(checkpoint["order_predictions"])
            if checkpoint is not None
            else aggregate_order_predictions(item_predictions)
        )
        # This is deliberately before bootstrap: an interrupted expensive finalization
        # can recover predictions, but only under the exact same data and selection lock.
        _write_recovery_checkpoint(
            output_root,
            item_predictions,
            order_predictions,
            _dataset_hashes(data_path),
            cast(str, selection_record["lock"]),
        )
        metrics = {
            "item": item_metrics,
            "order": order_classification_metrics(order_predictions, threshold["medium_from"]),
            "bootstrap": {
                "item_average_precision": bootstrap_average_precision(
                    y_test.tolist(),
                    test_probability.tolist(),
                    iterations=settings.bootstrap_iterations,
                    seed=settings.seed,
                    order_ids=partitions.test["order_id"].tolist(),
                ),
                "order_average_precision": bootstrap_average_precision(
                    order_predictions["label"].tolist(),
                    order_predictions["priority_score"].tolist(),
                    iterations=settings.bootstrap_iterations,
                    seed=settings.seed,
                    order_ids=order_predictions["order_id"].tolist(),
                ),
            },
        }
        priorities = budget_metrics(
            order_predictions["label"].tolist(),
            order_predictions["priority_score"].tolist(),
            order_predictions["order_value"].tolist(),
            settings.budgets,
        )

    report: dict[str, Any] = {
        "evaluation_status": "exploratory_non_confirmatory" if finalize_test else "development",
        "data": {
            "path": str(data_path),
            "sha256": _sha256(data_path),
            "rows": len(frame),
        },
        "config": _json_safe_config(settings),
        "partitions": partition_summary(partitions),
        "selection_average_precision": selection_scores,
        "selection_average_precision_std": selection_standard_deviation,
        "rolling_validation": fold_scores,
        "selected_model": selected_name.split("-", 1)[0],
        "selected_variant": selected_name,
        "selected_regime": selected_regime,
        "calibration_method": calibration_method,
        "calibration_brier_scores": calibration_scores,
        "threshold_policy": threshold,
        "selection_record": selection_record,
        "candidate_comparison": _candidate_comparison(
            order_average_precision, order_brier, candidates, fold_scores
        ),
        "dataset_hashes": _dataset_hashes(data_path),
        "reproducibility": _reproducibility_metadata(),
        "feature_schema": list(FEATURES),
    }
    if finalize_test:
        # The sealed test partition is deliberately absent from development
        # reports.  Do not even construct diagnostics until the finalization
        # gate above has accepted the frozen selection and lock.
        report.update(
            {
                "test_metrics": metrics,
                "budget_metrics": priorities,
                "test_diagnostics": _test_diagnostics(partitions.test, test_probability),
            }
        )
        _write_artifacts(
            output_root, selected, item_predictions, order_predictions, report, settings
        )
        _write_attempt_metadata(
            output_root, selection_record, _dataset_hashes(data_path), "completed"
        )
    return report


def _fit_kwargs(frame: pd.DataFrame, regime: str) -> dict[str, Any]:
    if regime == "item_unweighted":
        return {}
    if regime == "order_weight":
        weights = frame.groupby("order_id")["order_id"].transform(lambda x: 1 / len(x))
        return {"sample_weight": weights.to_numpy()}
    return {}


def _training_frame(frame: pd.DataFrame, regime: str) -> pd.DataFrame:
    """Fit order_reference on one stable product representative per order."""
    if regime != "order_reference":
        return frame
    return (
        frame.sort_values(["order_id", "product_item_id"], kind="mergesort")
        .drop_duplicates("order_id", keep="first")
        .reset_index(drop=True)
    )


def _candidate_comparison(
    order_pr_auc: dict[str, list[float]],
    order_brier: dict[str, list[float]],
    candidates: dict[str, BaseEstimator],
    fold_scores: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    """Return a stable, auditable comparison table for every regime and variant."""
    rows = []
    for key in order_pr_auc:
        regime, variant_id = key.split(":", 1)
        params = candidates[variant_id].get_params(deep=True)
        rows.append(
            {
                "regime": regime,
                "variant_id": variant_id,
                "parameters": {
                    str(k): str(v) for k, v in sorted(params.items()) if k.startswith("model__")
                },
                "order_max_v1_pr_auc": float(np.mean(order_pr_auc[key])),
                "brier_score": float(np.mean(order_brier[key])),
                "folds": fold_scores[key],
            }
        )
    return rows


def _order_max(frame: pd.DataFrame, probability: np.ndarray) -> tuple[pd.Series, np.ndarray]:
    x = frame[["order_id", TARGET]].copy()
    x["p"] = probability
    grouped = x.groupby("order_id", sort=True)
    labels = cast(pd.Series, grouped[TARGET].max())
    probabilities = np.asarray(grouped["p"].max(), dtype=float)
    return labels, probabilities


def _capacity_thresholds(frame: pd.DataFrame, probability: np.ndarray) -> dict[str, Any]:
    x = (
        pd.DataFrame({"order_id": frame.order_id, "p": probability})
        .groupby("order_id", sort=True)
        .p.max()
    )
    medium = float(x.nlargest(max(1, int(np.ceil(len(x) * 0.20))), keep="first").min())
    high = float(x.nlargest(max(1, int(np.ceil(len(x) * 0.05))), keep="first").min())
    if high <= medium:
        high = float(np.nextafter(medium, np.inf))
    return {
        "medium_from": medium,
        "high_from": high,
        "policy": "top20_top5_order_probability",
    }


def _selection_lock(*values: object) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()


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
    root: Path,
    estimator: BaseEstimator,
    item_predictions: pd.DataFrame,
    order_predictions: pd.DataFrame,
    report: dict[str, Any],
    settings: TrainingConfig,
) -> None:
    model_path = root / "artifacts/models/hidden_dissatisfaction.joblib"
    item_path = root / "artifacts/predictions/test_item_predictions.csv"
    order_path = root / "artifacts/predictions/test_order_predictions.csv"
    report_path = root / "reports/experiments/latest.json"
    extras = {
        root / "artifacts/config/frozen_config.json": report["config"],
        root / "artifacts/selection/candidate_fold_comparison.json": report["candidate_comparison"],
        root / "artifacts/selection/selected_policy.json": report["selection_record"],
        root / "artifacts/reproducibility/environment.json": report["reproducibility"],
        root / "artifacts/metrics/final_metrics.json": report.get("test_metrics", {}),
    }
    for path in (*extras, model_path, item_path, order_path, report_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    for path, value in extras.items():
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    joblib.dump(estimator, model_path)
    item_predictions.to_csv(item_path, index=False)
    order_predictions.to_csv(order_path, index=False)
    report["artifact_inventory"] = {
        str(path.relative_to(root)): _sha256(path)
        for path in (*extras, model_path, item_path, order_path)
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _write_recovery_checkpoint(
    root: Path,
    item_predictions: pd.DataFrame,
    order_predictions: pd.DataFrame,
    dataset_hashes: dict[str, str],
    selection_lock: str,
) -> None:
    path = root / "artifacts/checkpoints/test_finalization.recovery.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "TEST_FINALIZATION_RECOVERY_CHECKPOINT",
        "selection_lock": selection_lock,
        "dataset_hashes": dataset_hashes,
        "item_predictions": item_predictions.to_dict(orient="records"),
        "order_predictions": order_predictions.to_dict(orient="records"),
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _write_attempt_metadata(
    root: Path, selection: dict[str, Any], hashes: dict[str, str], state: str
) -> None:
    path = root / "artifacts/checkpoints/test_finalization.attempts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
                    "state": state,
                    "selection_lock": selection.get("lock"),
                    "dataset_hashes": hashes,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            + "\n"
        )


def _read_recovery_checkpoint(
    root: Path, dataset_hashes: dict[str, str], selection_lock: str
) -> dict[str, Any] | None:
    """Read only a checkpoint matching the immutable finalization inputs."""
    path = root / "artifacts/checkpoints/test_finalization.recovery.json"
    if not path.exists():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not all(isinstance(key, str) for key in loaded):
        raise ValueError("recovery checkpoint must contain a JSON object")
    payload = cast(dict[str, Any], loaded)
    if (
        payload.get("kind") != "TEST_FINALIZATION_RECOVERY_CHECKPOINT"
        or payload.get("dataset_hashes") != dataset_hashes
        or payload.get("selection_lock") != selection_lock
    ):
        raise ValueError("recovery checkpoint hashes or selection lock do not match")
    return payload


def _dataset_hashes(path: Path) -> dict[str, str]:
    hashes = {"dataset": _sha256(path)}
    for candidate in (
        path.with_name(path.name + ".manifest.json"),
        path.with_suffix(path.suffix + ".manifest"),
        path.with_suffix(".manifest.json"),
    ):
        if candidate.exists():
            hashes["manifest"] = _sha256(candidate)
            break
    return hashes


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


def _test_diagnostics(frame: pd.DataFrame, probability: np.ndarray) -> dict[str, object]:
    diagnostic = frame.copy()
    diagnostic["predicted_probability"] = probability
    diagnostic["month"] = diagnostic["prediction_at"].dt.to_period("M").astype(str)

    monthly: dict[str, dict[str, float | int]] = {}
    for month, group in diagnostic.groupby("month"):
        monthly[str(month)] = {
            "rows": len(group),
            "prevalence": float(np.asarray(group[TARGET].mean()).item()),
            "average_precision": float(
                average_precision_score(group[TARGET], group["predicted_probability"])
            ),
        }

    calibration: list[dict[str, float | int]] = []
    bins = pd.qcut(diagnostic["predicted_probability"], q=10, duplicates="drop")
    for _, group in diagnostic.groupby(bins, observed=True):
        calibration.append(
            {
                "rows": len(group),
                "mean_probability": float(np.asarray(group["predicted_probability"].mean()).item()),
                "observed_rate": float(np.asarray(group[TARGET].mean()).item()),
            }
        )

    subgroups: dict[str, list[dict[str, float | int | str]]] = {}
    for feature in CATEGORICAL_FEATURES:
        rows: list[dict[str, float | int | str]] = []
        for value, group in diagnostic.groupby(feature, observed=True):
            if len(group) < 300 or group[TARGET].nunique() != 2:
                continue
            rows.append(
                {
                    "value": str(value),
                    "rows": len(group),
                    "prevalence": float(np.asarray(group[TARGET].mean()).item()),
                    "average_precision": float(
                        average_precision_score(group[TARGET], group["predicted_probability"])
                    ),
                }
            )
        subgroups[feature] = sorted(rows, key=lambda row: float(row["average_precision"]))
    return {"monthly": monthly, "calibration_deciles": calibration, "subgroups": subgroups}


def _reproducibility_metadata() -> dict[str, object]:
    packages: dict[str, str | None] = {}
    for package in ("catboost", "joblib", "numpy", "pandas", "pyarrow", "scikit-learn"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    )
    relevant = sorted(
        Path(p) for p in ("src", "configs", "pyproject.toml", "uv.lock") if Path(p).exists()
    )
    digest = hashlib.sha256()
    for path in relevant:
        files = (
            [path] if path.is_file() else sorted(path.rglob("*.py")) + sorted(path.rglob("*.toml"))
        )
        for file in files:
            digest.update(str(file).encode())
            digest.update(file.read_bytes())
    return {
        "git_commit": commit.stdout.strip() or None,
        "working_tree_dirty": bool(dirty.stdout.strip()),
        "packages": packages,
        "source_snapshot_sha256": digest.hexdigest(),
    }
