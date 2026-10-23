"""Candidate estimator pipelines whose preprocessing is fitted within each fold."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from hidden_dissatisfaction.modeling.schema import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


class PrevalenceClassifier(ClassifierMixin, BaseEstimator):
    """Constant-probability baseline learned only from the training labels."""

    prevalence_: float
    classes_: np.ndarray

    def fit(
        self, X: object, y: object, sample_weight: object | None = None
    ) -> PrevalenceClassifier:
        """Learn training prevalence."""
        values = np.asarray(y, dtype=float)
        if sample_weight is None:
            self.prevalence_ = float(values.mean())
        else:
            weights = np.asarray(sample_weight, dtype=float)
            if weights.ndim != 1 or len(weights) != len(values):
                raise ValueError("sample_weight must have one nonnegative value per label")
            if not np.all(np.isfinite(weights)) or np.any(weights < 0):
                raise ValueError("sample_weight must contain only finite, nonnegative values")
            total = float(weights.sum())
            if total <= 0:
                raise ValueError("sample_weight must have a positive total")
            self.prevalence_ = float(np.dot(values, weights) / total)
        self.classes_ = np.asarray([0, 1])
        return self

    def predict_proba(self, X: object) -> np.ndarray:
        """Return the training prevalence for every sample."""
        count = len(X)  # type: ignore[arg-type]
        positive = np.full(count, self.prevalence_)
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X: object) -> np.ndarray:
        """Apply the conventional 0.5 threshold."""
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


class _SampleWeightPipeline(Pipeline):
    """Pipeline that forwards item weights only to its final estimator."""

    def fit(
        self,
        X: object,
        y: object | None = None,
        sample_weight: object | None = None,
        **fit_params: object,
    ) -> _SampleWeightPipeline:
        if sample_weight is not None:
            fit_params["model__sample_weight"] = sample_weight
        super().fit(X, y, **fit_params)
        return self


def build_candidates(seed: int) -> dict[str, BaseEstimator]:
    """Construct the seven versioned, bounded, deterministic candidates."""
    one_hot = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    tree_one_hot = ColumnTransformer(
        [
            (
                "numeric",
                SimpleImputer(strategy="median"),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    ordinal = ColumnTransformer(
        [
            (
                "numeric",
                SimpleImputer(strategy="median"),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "encode",
                            OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                        ),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    candidates: dict[str, BaseEstimator] = {
        "prevalence-v1": PrevalenceClassifier(),
        "logistic-c0_1-v1": _SampleWeightPipeline(
            [
                ("preprocess", one_hot),
                (
                    "model",
                    LogisticRegression(
                        C=0.1, class_weight="balanced", max_iter=2_000, random_state=seed
                    ),
                ),
            ]
        ),
        "random_forest-depth8-leaf5-v1": _SampleWeightPipeline(
            [
                ("preprocess", tree_one_hot),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200,
                        min_samples_leaf=5,
                        max_depth=8,
                        class_weight="balanced_subsample",
                        n_jobs=1,
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting-l2-1-leaf31-v1": _SampleWeightPipeline(
            [
                ("preprocess", ordinal),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.08,
                        max_iter=250,
                        max_leaf_nodes=31,
                        l2_regularization=1.0,
                        class_weight="balanced",
                        categorical_features=[False]
                        * (len(NUMERIC_FEATURES) + len(BINARY_FEATURES))
                        + [True] * len(CATEGORICAL_FEATURES),
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }
    candidates["logistic-c1-v1"] = _SampleWeightPipeline(
        [
            ("preprocess", one_hot),
            (
                "model",
                LogisticRegression(
                    C=1.0, class_weight="balanced", max_iter=2_000, random_state=seed
                ),
            ),
        ]
    )
    candidates["random_forest-depth12-leaf10-v1"] = _SampleWeightPipeline(
        [
            ("preprocess", tree_one_hot),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=200,
                    min_samples_leaf=10,
                    max_depth=12,
                    class_weight="balanced_subsample",
                    n_jobs=1,
                    random_state=seed,
                ),
            ),
        ]
    )
    candidates["hist_gradient_boosting-l2-5-leaf15-v1"] = _SampleWeightPipeline(
        [
            ("preprocess", ordinal),
            (
                "model",
                HistGradientBoostingClassifier(
                    learning_rate=0.08,
                    max_iter=250,
                    max_leaf_nodes=15,
                    l2_regularization=5.0,
                    class_weight="balanced",
                    categorical_features=[False] * (len(NUMERIC_FEATURES) + len(BINARY_FEATURES))
                    + [True] * len(CATEGORICAL_FEATURES),
                    random_state=seed,
                ),
            ),
        ]
    )
    return candidates
